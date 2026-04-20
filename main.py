"""
Contract Radar — Vendor contract & subscription expiry tracker with renewal alerts.
SMBs use this to centralize all their software/vendor contracts and never miss a renewal.
"""

import os
import uuid
from datetime import datetime, timedelta, date
from typing import Optional
from fastapi import FastAPI, HTTPException, Depends, Header, BackgroundTasks
from fastapi.responses import HTMLResponse
from models import Contract, ContractCreate, ContractUpdate, ContactInfo, AlertSettings
from notifier import send_expiry_alert, send_summary_report
from database import db

app = FastAPI(
    title="Contract Radar",
    version="1.0.0",
    description="Never miss a contract renewal or subscription expiry again",
)

ADMIN_KEY = os.getenv("ADMIN_API_KEY", "changeme")


def require_admin(x_api_key: str = Header(...)):
    if x_api_key != ADMIN_KEY:
        raise HTTPException(403, "Invalid API key")


# ── Health ───────────────────────────────────────────────────────────────────

@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.utcnow().isoformat()}


# ── Contracts ─────────────────────────────────────────────────────────────────

@app.post("/contracts", response_model=Contract)
def create_contract(body: ContractCreate, _=Depends(require_admin)):
    contract_id = str(uuid.uuid4())
    expiry = datetime.fromisoformat(body.expiry_date).date()
    today = date.today()
    days_until_expiry = (expiry - today).days

    contract = Contract(
        id=contract_id,
        vendor_name=body.vendor_name,
        contract_type=body.contract_type,
        description=body.description,
        annual_value=body.annual_value,
        currency=body.currency,
        start_date=body.start_date,
        expiry_date=body.expiry_date,
        auto_renews=body.auto_renews,
        renewal_notice_days=body.renewal_notice_days,
        owner_name=body.owner_name,
        owner_email=body.owner_email,
        tags=body.tags,
        status="active" if days_until_expiry > 0 else "expired",
        days_until_expiry=days_until_expiry,
        created_at=datetime.utcnow().isoformat(),
        notes=body.notes,
    )
    db["contracts"][contract_id] = contract.dict()
    return contract


@app.get("/contracts", response_model=list[Contract])
def list_contracts(
    status: Optional[str] = None,
    contract_type: Optional[str] = None,
    expiring_within_days: Optional[int] = None,
    _=Depends(require_admin),
):
    contracts = list(db["contracts"].values())
    _refresh_days(contracts)

    if status:
        contracts = [c for c in contracts if c["status"] == status]
    if contract_type:
        contracts = [c for c in contracts if c["contract_type"] == contract_type]
    if expiring_within_days is not None:
        contracts = [c for c in contracts if 0 <= c["days_until_expiry"] <= expiring_within_days]

    contracts.sort(key=lambda c: c["days_until_expiry"])
    return [Contract(**c) for c in contracts]


@app.get("/contracts/{contract_id}", response_model=Contract)
def get_contract(contract_id: str, _=Depends(require_admin)):
    c = db["contracts"].get(contract_id)
    if not c:
        raise HTTPException(404, "Contract not found")
    _refresh_days([c])
    return Contract(**c)


@app.patch("/contracts/{contract_id}", response_model=Contract)
def update_contract(contract_id: str, body: ContractUpdate, _=Depends(require_admin)):
    c = db["contracts"].get(contract_id)
    if not c:
        raise HTTPException(404, "Contract not found")
    updates = body.dict(exclude_none=True)
    c.update(updates)
    _refresh_days([c])
    return Contract(**c)


@app.delete("/contracts/{contract_id}")
def delete_contract(contract_id: str, _=Depends(require_admin)):
    if contract_id not in db["contracts"]:
        raise HTTPException(404, "Contract not found")
    del db["contracts"][contract_id]
    return {"deleted": True}


# ── Dashboard & Analytics ─────────────────────────────────────────────────────

@app.get("/dashboard")
def dashboard(_=Depends(require_admin)):
    contracts = list(db["contracts"].values())
    _refresh_days(contracts)

    today = date.today()
    expiring_30 = [c for c in contracts if 0 <= c["days_until_expiry"] <= 30]
    expiring_90 = [c for c in contracts if 0 <= c["days_until_expiry"] <= 90]
    expired = [c for c in contracts if c["days_until_expiry"] < 0]
    active = [c for c in contracts if c["status"] == "active"]

    total_annual_value = sum(c.get("annual_value") or 0 for c in active)
    at_risk_value = sum(c.get("annual_value") or 0 for c in expiring_90)

    return {
        "total_contracts": len(contracts),
        "active": len(active),
        "expired": len(expired),
        "expiring_within_30_days": len(expiring_30),
        "expiring_within_90_days": len(expiring_90),
        "total_annual_value": total_annual_value,
        "annual_value_at_risk_90d": at_risk_value,
        "upcoming_renewals": sorted(
            [{"id": c["id"], "vendor": c["vendor_name"], "days": c["days_until_expiry"],
              "value": c.get("annual_value"), "auto_renews": c.get("auto_renews")}
             for c in expiring_30],
            key=lambda x: x["days"]
        ),
    }


@app.get("/contracts/report/calendar")
def renewal_calendar(months_ahead: int = 3, _=Depends(require_admin)):
    """Group upcoming renewals by month."""
    contracts = list(db["contracts"].values())
    _refresh_days(contracts)
    today = date.today()
    cutoff = today + timedelta(days=months_ahead * 30)
    upcoming = [c for c in contracts if 0 <= c["days_until_expiry"] <= (months_ahead * 30)]

    by_month: dict = {}
    for c in upcoming:
        expiry = datetime.fromisoformat(c["expiry_date"]).date()
        month_key = expiry.strftime("%Y-%m")
        by_month.setdefault(month_key, []).append({
            "id": c["id"],
            "vendor": c["vendor_name"],
            "expiry_date": c["expiry_date"],
            "auto_renews": c.get("auto_renews"),
            "annual_value": c.get("annual_value"),
            "owner_email": c.get("owner_email"),
        })

    return {"calendar": by_month, "total_upcoming": len(upcoming)}


# ── Alerts ────────────────────────────────────────────────────────────────────

@app.post("/alerts/check")
async def check_and_alert(settings: AlertSettings, background_tasks: BackgroundTasks, _=Depends(require_admin)):
    """Trigger expiry alerts for contracts within the notice window."""
    contracts = list(db["contracts"].values())
    _refresh_days(contracts)

    alerted = []
    for c in contracts:
        notice_days = c.get("renewal_notice_days") or settings.default_notice_days
        if 0 <= c["days_until_expiry"] <= notice_days:
            background_tasks.add_task(
                send_expiry_alert,
                c,
                settings.alert_email or c.get("owner_email"),
            )
            alerted.append(c["vendor_name"])

    return {"alerted_count": len(alerted), "alerted_vendors": alerted}


@app.post("/alerts/summary")
async def send_weekly_summary(contact: ContactInfo, background_tasks: BackgroundTasks, _=Depends(require_admin)):
    contracts = list(db["contracts"].values())
    _refresh_days(contracts)
    background_tasks.add_task(send_summary_report, contracts, contact.email, contact.name)
    return {"message": f"Weekly summary queued for {contact.email}"}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _refresh_days(contracts: list):
    today = date.today()
    for c in contracts:
        expiry = datetime.fromisoformat(c["expiry_date"]).date()
        c["days_until_expiry"] = (expiry - today).days
        c["status"] = "active" if c["days_until_expiry"] > 0 else "expired"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002, reload=True)
