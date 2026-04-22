import os
from datetime import datetime, timedelta
from typing import Optional, List

from fastapi import FastAPI, HTTPException, BackgroundTasks, UploadFile, File, Form
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from dotenv import load_dotenv

from database import init_db, get_db
from parser import extract_dates_from_text
from email_service import send_expiry_alerts

load_dotenv()

app = FastAPI(title="Contract Radar", description="Contract expiry tracker with renewal alerts")
scheduler = BackgroundScheduler()


class ContractCreate(BaseModel):
    title: str
    counterparty: str
    email_alerts: Optional[str] = None
    contract_text: Optional[str] = None
    start_date: Optional[str] = None
    end_date: str
    renewal_type: str = "manual"  # manual, auto-renew, one-time
    value: Optional[float] = None
    currency: str = "USD"
    notes: Optional[str] = None
    reminder_days: str = "30,14,7"  # Comma-separated days before expiry to alert


class ContractUpdate(BaseModel):
    title: Optional[str] = None
    end_date: Optional[str] = None
    email_alerts: Optional[str] = None
    notes: Optional[str] = None
    status: Optional[str] = None
    reminder_days: Optional[str] = None


@app.on_event("startup")
def startup():
    init_db()
    scheduler.add_job(
        run_expiry_checks,
        CronTrigger(hour=8, minute=0),
        id="daily_expiry_check",
        replace_existing=True,
    )
    scheduler.start()
    print("Contract Radar started — daily expiry check at 8am UTC")


@app.on_event("shutdown")
def shutdown():
    scheduler.shutdown()


def run_expiry_checks():
    today = datetime.utcnow().date()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM contracts WHERE status = 'active'")
        cols = [d[0] for d in c.description]
        contracts = [dict(zip(cols, r)) for r in c.fetchall()]

    alerts_to_send = []
    for contract in contracts:
        end = datetime.strptime(contract["end_date"], "%Y-%m-%d").date()
        days_left = (end - today).days
        reminder_days = [int(d.strip()) for d in contract.get("reminder_days", "30,14,7").split(",")]

        for threshold in reminder_days:
            if days_left == threshold:
                alerts_to_send.append((contract, days_left))
                break

        if days_left < 0:
            with get_db() as conn:
                conn.execute(
                    "UPDATE contracts SET status = 'expired' WHERE id = ?", (contract["id"],)
                )
                conn.commit()

    if alerts_to_send:
        send_expiry_alerts(alerts_to_send)
        print(f"[Alerts] Sent {len(alerts_to_send)} contract expiry alerts")


@app.get("/", response_class=HTMLResponse)
def dashboard():
    today = datetime.utcnow().date()
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM contracts ORDER BY end_date ASC")
        cols = [d[0] for d in c.description]
        contracts = [dict(zip(cols, r)) for r in c.fetchall()]

    rows = ""
    for ct in contracts:
        end = datetime.strptime(ct["end_date"], "%Y-%m-%d").date()
        days_left = (end - today).days

        if ct["status"] == "expired" or days_left < 0:
            urgency_color = "#95a5a6"
            urgency_label = "Expired"
            days_label = f"{abs(days_left)}d ago"
        elif days_left <= 7:
            urgency_color = "#e74c3c"
            urgency_label = "Critical"
            days_label = f"{days_left}d left"
        elif days_left <= 30:
            urgency_color = "#e67e22"
            urgency_label = "Expiring Soon"
            days_label = f"{days_left}d left"
        elif days_left <= 90:
            urgency_color = "#f39c12"
            urgency_label = "Watch"
            days_label = f"{days_left}d left"
        else:
            urgency_color = "#27ae60"
            urgency_label = "Active"
            days_label = f"{days_left}d left"

        value_str = f"{ct.get('currency','USD')} {ct.get('value') or 0:,.0f}" if ct.get("value") else "—"

        rows += f"""<tr>
            <td><strong>{ct['title']}</strong><br><span style='color:#999;font-size:12px'>{ct.get('notes','')[:60]}</span></td>
            <td>{ct['counterparty']}</td>
            <td>{ct.get('start_date','—')}</td>
            <td>{ct['end_date']}</td>
            <td><span style='font-weight:bold;color:{urgency_color}'>{days_label}</span></td>
            <td><span style='background:{urgency_color};color:white;padding:2px 8px;border-radius:10px;font-size:11px'>{urgency_label}</span></td>
            <td>{value_str}</td>
            <td>{ct.get('renewal_type','—')}</td>
            <td style='font-size:12px;color:#666'>{ct.get('email_alerts','—')}</td>
            <td>
                <button onclick='deleteContract({ct["id"]})' style='color:white;background:#e74c3c;border:none;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:12px'>Delete</button>
                {f'<button onclick="renewContract({ct["id"]})" style="color:white;background:#27ae60;border:none;padding:4px 10px;border-radius:4px;cursor:pointer;font-size:12px;margin-left:4px">Renew</button>' if ct["status"] != "expired" else ""}
            </td>
        </tr>"""

    expiring_30 = len([c for c in contracts if 0 <= (datetime.strptime(c["end_date"], "%Y-%m-%d").date() - today).days <= 30])
    expired = len([c for c in contracts if c["status"] == "expired"])

    return f"""<!DOCTYPE html>
<html><head><title>Contract Radar</title><meta charset='utf-8'>
<style>
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; margin:0; background:#f5f7fa; }}
  .header {{ background:linear-gradient(135deg,#2c3e50,#34495e); color:white; padding:20px 40px; }}
  .header h1 {{ margin:0; font-size:24px; }}
  .container {{ max-width:1400px; margin:28px auto; padding:0 24px; }}
  .stats {{ display:grid; grid-template-columns:repeat(4,1fr); gap:16px; margin-bottom:24px; }}
  .stat {{ background:white; padding:20px; border-radius:10px; box-shadow:0 2px 8px rgba(0,0,0,0.06); }}
  .stat .num {{ font-size:32px; font-weight:bold; }}
  .stat.warn .num {{ color:#e67e22; }}
  .stat.danger .num {{ color:#e74c3c; }}
  .card {{ background:white; border-radius:10px; padding:24px; box-shadow:0 2px 8px rgba(0,0,0,0.06); margin-bottom:24px; }}
  h2 {{ font-size:15px; color:#2c3e50; margin:0 0 16px; }}
  table {{ width:100%; border-collapse:collapse; font-size:13px; }}
  th {{ background:#f8f9fa; padding:9px 10px; text-align:left; font-size:11px; color:#666; text-transform:uppercase; letter-spacing:0.5px; border-bottom:2px solid #eee; }}
  td {{ padding:9px 10px; border-bottom:1px solid #f5f5f5; vertical-align:top; }}
  tr:hover {{ background:#fafafa; }}
  input, select, textarea {{ width:100%; padding:8px 10px; border:1px solid #ddd; border-radius:6px; font-size:13px; box-sizing:border-box; }}
  .btn {{ padding:9px 18px; background:#2c3e50; color:white; border:none; border-radius:6px; cursor:pointer; font-size:13px; }}
  .grid {{ display:grid; grid-template-columns:1fr 1fr; gap:12px; }}
  label {{ font-size:12px; color:#555; margin-bottom:3px; display:block; margin-top:10px; }}
</style>
</head><body>
<div class='header'>
  <h1>📡 Contract Radar</h1>
  <p style='margin:4px 0 0;opacity:0.8;font-size:13px'>Never miss a contract renewal or expiry</p>
</div>
<div class='container'>
  <div class='stats'>
    <div class='stat'><div class='num'>{len(contracts)}</div><div style='color:#999;font-size:13px'>Total Contracts</div></div>
    <div class='stat warn'><div class='num'>{expiring_30}</div><div style='color:#999;font-size:13px'>Expiring in 30 Days</div></div>
    <div class='stat danger'><div class='num'>{expired}</div><div style='color:#999;font-size:13px'>Expired</div></div>
    <div class='stat'><div class='num'>${sum(c.get("value") or 0 for c in contracts):,.0f}</div><div style='color:#999;font-size:13px'>Total Contract Value</div></div>
  </div>

  <div class='card'>
    <h2>Add Contract</h2>
    <div class='grid'>
      <div>
        <label>Contract Title *</label>
        <input id='title' placeholder='AWS Service Agreement' />
        <label>Counterparty (Vendor/Client) *</label>
        <input id='counterparty' placeholder='Amazon Web Services' />
        <label>End Date (Expiry) *</label>
        <input id='end_date' type='date' />
        <label>Start Date</label>
        <input id='start_date' type='date' />
      </div>
      <div>
        <label>Contract Value</label>
        <input id='value' type='number' placeholder='10000' />
        <label>Renewal Type</label>
        <select id='renewal_type'>
          <option value='manual'>Manual Renewal</option>
          <option value='auto-renew'>Auto-Renew</option>
          <option value='one-time'>One-Time</option>
        </select>
        <label>Alert Email(s) (comma-separated)</label>
        <input id='email_alerts' placeholder='legal@co.com, ops@co.com' />
        <label>Reminder Days Before Expiry</label>
        <input id='reminder_days' value='30,14,7' />
      </div>
    </div>
    <label>Paste Contract Text (optional — auto-extracts dates)</label>
    <textarea id='contract_text' rows='3' placeholder='Paste contract text here to auto-extract dates...'></textarea>
    <br/><br/>
    <button class='btn' onclick='addContract()'>Add Contract</button>
    <button class='btn' onclick='runChecks()' style='margin-left:8px;background:#e74c3c'>🔔 Run Alert Check Now</button>
    <div id='msg' style='margin-top:10px;font-size:13px'></div>
  </div>

  <div class='card'>
    <h2>Contract Registry</h2>
    <table>
      <tr>
        <th>Contract</th><th>Counterparty</th><th>Start</th><th>Expiry</th>
        <th>Time Left</th><th>Status</th><th>Value</th><th>Renewal</th><th>Alerts</th><th>Actions</th>
      </tr>
      {rows or "<tr><td colspan='10' style='text-align:center;color:#999;padding:32px'>No contracts added yet.</td></tr>"}
    </table>
  </div>
</div>
<script>
async function addContract() {{
  const text = document.getElementById('contract_text').value.trim();
  let endDate = document.getElementById('end_date').value;

  if (text && !endDate) {{
    const res = await fetch('/extract-dates', {{
      method: 'POST',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{text}})
    }});
    const data = await res.json();
    if (data.end_date) {{
      endDate = data.end_date;
      document.getElementById('end_date').value = endDate;
    }}
  }}

  if (!document.getElementById('title').value || !document.getElementById('counterparty').value || !endDate) {{
    document.getElementById('msg').innerHTML = '<span style="color:#e74c3c">Please fill in title, counterparty, and end date.</span>';
    return;
  }}

  const body = {{
    title: document.getElementById('title').value,
    counterparty: document.getElementById('counterparty').value,
    end_date: endDate,
    start_date: document.getElementById('start_date').value || null,
    value: parseFloat(document.getElementById('value').value) || null,
    renewal_type: document.getElementById('renewal_type').value,
    email_alerts: document.getElementById('email_alerts').value || null,
    reminder_days: document.getElementById('reminder_days').value || '30,14,7',
    contract_text: text || null,
  }};

  const res = await fetch('/contracts', {{method:'POST', headers:{{'Content-Type':'application/json'}}, body: JSON.stringify(body)}});
  const data = await res.json();
  if (res.ok) {{
    document.getElementById('msg').innerHTML = '<span style="color:#27ae60">✅ Contract added!</span>';
    setTimeout(() => location.reload(), 1000);
  }} else {{
    document.getElementById('msg').innerHTML = `<span style="color:#e74c3c">Error: ${{data.detail}}</span>`;
  }}
}}

async function deleteContract(id) {{
  if (confirm('Delete this contract?')) {{
    await fetch('/contracts/' + id, {{method: 'DELETE'}});
    location.reload();
  }}
}}

async function renewContract(id) {{
  const newDate = prompt('Enter new expiry date (YYYY-MM-DD):');
  if (newDate) {{
    await fetch('/contracts/' + id, {{
      method: 'PATCH',
      headers: {{'Content-Type': 'application/json'}},
      body: JSON.stringify({{end_date: newDate, status: 'active'}})
    }});
    location.reload();
  }}
}}

async function runChecks() {{
  const res = await fetch('/alerts/run', {{method: 'POST'}});
  const data = await res.json();
  alert(data.message);
}}
</script>
</body></html>"""


@app.post("/contracts", status_code=201)
def create_contract(contract: ContractCreate):
    try:
        datetime.strptime(contract.end_date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="end_date must be YYYY-MM-DD")

    extracted_dates = {}
    if contract.contract_text:
        extracted_dates = extract_dates_from_text(contract.contract_text)

    with get_db() as conn:
        c = conn.cursor()
        c.execute("""
            INSERT INTO contracts (title, counterparty, email_alerts, start_date, end_date,
                renewal_type, value, currency, notes, reminder_days, extracted_dates)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        """, (
            contract.title, contract.counterparty, contract.email_alerts,
            contract.start_date or extracted_dates.get("start_date"),
            contract.end_date,
            contract.renewal_type, contract.value, contract.currency,
            contract.notes, contract.reminder_days,
            str(extracted_dates) if extracted_dates else None
        ))
        conn.commit()
        return {"id": c.lastrowid, "message": "Contract added", "extracted_dates": extracted_dates}


@app.get("/contracts")
def list_contracts(status: Optional[str] = None):
    with get_db() as conn:
        c = conn.cursor()
        if status:
            c.execute("SELECT * FROM contracts WHERE status = ? ORDER BY end_date ASC", (status,))
        else:
            c.execute("SELECT * FROM contracts ORDER BY end_date ASC")
        cols = [d[0] for d in c.description]
        return [dict(zip(cols, r)) for r in c.fetchall()]


@app.patch("/contracts/{contract_id}")
def update_contract(contract_id: int, update: ContractUpdate):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("SELECT * FROM contracts WHERE id = ?", (contract_id,))
        existing = c.fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Contract not found")
        cols = [d[0] for d in c.description]
        ct = dict(zip(cols, existing))

        c.execute("""UPDATE contracts SET title=?, end_date=?, email_alerts=?, notes=?, status=?, reminder_days=?
                     WHERE id=?""", (
            update.title or ct["title"],
            update.end_date or ct["end_date"],
            update.email_alerts if update.email_alerts is not None else ct["email_alerts"],
            update.notes if update.notes is not None else ct["notes"],
            update.status or ct["status"],
            update.reminder_days or ct["reminder_days"],
            contract_id
        ))
        conn.commit()
    return {"message": "Contract updated"}


@app.delete("/contracts/{contract_id}")
def delete_contract(contract_id: int):
    with get_db() as conn:
        c = conn.cursor()
        c.execute("DELETE FROM contracts WHERE id = ?", (contract_id,))
        if c.rowcount == 0:
            raise HTTPException(status_code=404, detail="Contract not found")
        conn.commit()
    return {"message": "Contract deleted"}


@app.post("/extract-dates")
def extract_dates(body: dict):
    text = body.get("text", "")
    if not text:
        raise HTTPException(status_code=400, detail="text is required")
    dates = extract_dates_from_text(text)
    return dates


@app.post("/alerts/run")
def trigger_alerts(background_tasks: BackgroundTasks):
    background_tasks.add_task(run_expiry_checks)
    return {"message": "Alert check triggered — notifications will be sent if contracts are expiring."}


@app.get("/upcoming")
def upcoming_expirations(days: int = 90):
    today = datetime.utcnow().date()
    cutoff = today + timedelta(days=days)
    with get_db() as conn:
        c = conn.cursor()
        c.execute(
            "SELECT * FROM contracts WHERE status = 'active' AND end_date <= ? ORDER BY end_date ASC",
            (cutoff.isoformat(),)
        )
        cols = [d[0] for d in c.description]
        contracts = [dict(zip(cols, r)) for r in c.fetchall()]

    for ct in contracts:
        end = datetime.strptime(ct["end_date"], "%Y-%m-%d").date()
        ct["days_until_expiry"] = (end - today).days
    return contracts


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
