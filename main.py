"""
Contract Radar - Vendor contract & subscription renewal alert tracker for SMBs
"""
import os
import sqlite3
import smtplib
import threading
import time
import csv
import io
from datetime import datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from fastapi import FastAPI, HTTPException, Request, Form, Depends, UploadFile, File
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
import uvicorn
from dotenv import load_dotenv

load_dotenv()

app = FastAPI(title="Contract Radar", description="Vendor contract renewal alert system")

DB_PATH = os.getenv("DB_PATH", "contracts.db")
SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
FROM_EMAIL = os.getenv("FROM_EMAIL", SMTP_USER)
ALERT_EMAIL = os.getenv("ALERT_EMAIL", SMTP_USER)
ALERT_DAYS = [int(d) for d in os.getenv("ALERT_DAYS", "60,30,14,7,1").split(",")]

templates = Jinja2Templates(directory="templates")


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS contracts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vendor_name TEXT NOT NULL,
            contract_name TEXT NOT NULL,
            category TEXT DEFAULT 'Other',
            start_date TEXT,
            end_date TEXT NOT NULL,
            renewal_date TEXT,
            amount REAL DEFAULT 0,
            currency TEXT DEFAULT 'USD',
            billing_cycle TEXT DEFAULT 'Annual',
            auto_renews INTEGER DEFAULT 0,
            notice_days INTEGER DEFAULT 30,
            owner_email TEXT,
            notes TEXT,
            status TEXT DEFAULT 'active',
            created_at TEXT DEFAULT (datetime('now'))
        );
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            contract_id INTEGER NOT NULL,
            alert_type TEXT NOT NULL,
            days_until_expiry INTEGER,
            sent_at TEXT DEFAULT (datetime('now')),
            FOREIGN KEY (contract_id) REFERENCES contracts(id)
        );
    """)
    conn.commit()
    conn.close()


def send_email(to_email: str, subject: str, body_html: str) -> bool:
    if not SMTP_USER or not SMTP_PASS:
        print(f"[EMAIL MOCK] To: {to_email} | Subject: {subject}")
        return True
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = FROM_EMAIL
        msg["To"] = to_email
        msg.attach(MIMEText(body_html, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
            server.starttls()
            server.login(SMTP_USER, SMTP_PASS)
            server.sendmail(FROM_EMAIL, to_email, msg.as_string())
        return True
    except Exception as e:
        print(f"Email error: {e}")
        return False


def build_alert_email(contracts_by_urgency: dict) -> str:
    rows = ""
    for urgency, contracts in contracts_by_urgency.items():
        color = {"critical": "#e74c3c", "warning": "#f39c12", "info": "#3498db"}.get(urgency, "#333")
        for c in contracts:
            days = c["days_until"]
            rows += f"""
            <tr>
              <td style="padding:12px;border-bottom:1px solid #eee;">{c['vendor_name']}</td>
              <td style="padding:12px;border-bottom:1px solid #eee;">{c['contract_name']}</td>
              <td style="padding:12px;border-bottom:1px solid #eee;">{c['end_date']}</td>
              <td style="padding:12px;border-bottom:1px solid #eee;color:{color};font-weight:600;">
                {"TODAY" if days == 0 else f"{days} day{'s' if days != 1 else ''}" if days > 0 else "EXPIRED"}
              </td>
              <td style="padding:12px;border-bottom:1px solid #eee;">{c['currency']} {c['amount']:,.0f}/yr</td>
              <td style="padding:12px;border-bottom:1px solid #eee;">{'⚠️ Auto-renews' if c['auto_renews'] else 'Manual'}</td>
            </tr>"""

    return f"""
    <html><body style="font-family:Arial,sans-serif;max-width:800px;margin:0 auto;padding:20px;">
    <div style="background:#1a1a2e;color:white;padding:24px;border-radius:12px 12px 0 0;">
      <h1 style="margin:0;font-size:1.4rem;">📡 Contract Radar Alert</h1>
      <p style="margin:8px 0 0;color:#a0aec0;font-size:0.9rem;">{datetime.now().strftime('%B %d, %Y')}</p>
    </div>
    <div style="background:white;padding:24px;border-radius:0 0 12px 12px;border:1px solid #e2e8f0;border-top:none;">
      <p>The following contracts require your attention:</p>
      <table style="width:100%;border-collapse:collapse;margin-top:16px;">
        <thead>
          <tr style="background:#f7fafc;font-size:0.8rem;color:#4a5568;">
            <th style="padding:10px 12px;text-align:left;">Vendor</th>
            <th style="padding:10px 12px;text-align:left;">Contract</th>
            <th style="padding:10px 12px;text-align:left;">Expires</th>
            <th style="padding:10px 12px;text-align:left;">Expires In</th>
            <th style="padding:10px 12px;text-align:left;">Value</th>
            <th style="padding:10px 12px;text-align:left;">Renewal</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
      <p style="color:#718096;font-size:0.8rem;margin-top:24px;">Sent by Contract Radar</p>
    </div>
    </body></html>"""


def check_and_send_alerts():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    today = datetime.now().date()

    contracts = conn.execute(
        "SELECT * FROM contracts WHERE status = 'active'"
    ).fetchall()

    to_alert = {"critical": [], "warning": [], "info": []}
    alerted_any = False

    for c in contracts:
        end = datetime.strptime(c["end_date"], "%Y-%m-%d").date()
        days_until = (end - today).days

        for threshold in ALERT_DAYS:
            if days_until == threshold:
                already_sent = conn.execute(
                    "SELECT id FROM alerts WHERE contract_id = ? AND days_until_expiry = ? AND date(sent_at) = date('now')",
                    (c["id"], threshold)
                ).fetchone()

                if not already_sent:
                    urgency = "critical" if threshold <= 7 else ("warning" if threshold <= 30 else "info")
                    to_alert[urgency].append({
                        **dict(c), "days_until": days_until
                    })
                    conn.execute(
                        "INSERT INTO alerts (contract_id, alert_type, days_until_expiry) VALUES (?, ?, ?)",
                        (c["id"], urgency, threshold)
                    )
                    alerted_any = True
                break

    if alerted_any:
        total = sum(len(v) for v in to_alert.values())
        subject = f"⚠️ Contract Radar: {total} contract{'s' if total > 1 else ''} need{'s' if total == 1 else ''} attention"
        html = build_alert_email(to_alert)
        alert_to = ALERT_EMAIL or SMTP_USER
        if alert_to:
            send_email(alert_to, subject, html)

    conn.commit()
    conn.close()


def alert_scheduler():
    while True:
        try:
            check_and_send_alerts()
        except Exception as e:
            print(f"Scheduler error: {e}")
        time.sleep(3600)


# ─── Routes ────────────────────────────────────────────────────────────────────

@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request, db: sqlite3.Connection = Depends(get_db)):
    contracts = db.execute("""
        SELECT *,
            julianday(end_date) - julianday('now') as days_until,
            CASE
                WHEN julianday(end_date) - julianday('now') <= 7 THEN 'critical'
                WHEN julianday(end_date) - julianday('now') <= 30 THEN 'warning'
                WHEN julianday(end_date) - julianday('now') <= 60 THEN 'attention'
                ELSE 'ok'
            END as urgency
        FROM contracts WHERE status = 'active'
        ORDER BY days_until ASC
    """).fetchall()

    stats = db.execute("""
        SELECT
            COUNT(*) as total,
            SUM(CASE WHEN julianday(end_date) - julianday('now') <= 30 THEN 1 ELSE 0 END) as expiring_soon,
            SUM(CASE WHEN julianday(end_date) - julianday('now') <= 0 THEN 1 ELSE 0 END) as expired,
            SUM(amount) as total_value,
            SUM(CASE WHEN auto_renews = 1 THEN 1 ELSE 0 END) as auto_renew_count
        FROM contracts WHERE status = 'active'
    """).fetchone()
    return templates.TemplateResponse("dashboard.html", {
        "request": request, "contracts": contracts, "stats": stats
    })


@app.post("/contracts", response_class=RedirectResponse)
async def create_contract(
    vendor_name: str = Form(...),
    contract_name: str = Form(...),
    category: str = Form("Other"),
    start_date: str = Form(""),
    end_date: str = Form(...),
    amount: float = Form(0),
    currency: str = Form("USD"),
    billing_cycle: str = Form("Annual"),
    auto_renews: int = Form(0),
    notice_days: int = Form(30),
    owner_email: str = Form(""),
    notes: str = Form(""),
    db: sqlite3.Connection = Depends(get_db)
):
    db.execute(
        """INSERT INTO contracts (vendor_name, contract_name, category, start_date, end_date,
           amount, currency, billing_cycle, auto_renews, notice_days, owner_email, notes)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (vendor_name, contract_name, category, start_date or None, end_date,
         amount, currency, billing_cycle, auto_renews, notice_days, owner_email, notes)
    )
    db.commit()
    return RedirectResponse("/", status_code=302)


@app.post("/contracts/{contract_id}/delete", response_class=RedirectResponse)
async def delete_contract(contract_id: int, db: sqlite3.Connection = Depends(get_db)):
    db.execute("UPDATE contracts SET status = 'archived' WHERE id = ?", (contract_id,))
    db.commit()
    return RedirectResponse("/", status_code=302)


@app.post("/contracts/{contract_id}/renew", response_class=RedirectResponse)
async def renew_contract(
    contract_id: int,
    new_end_date: str = Form(...),
    db: sqlite3.Connection = Depends(get_db)
):
    db.execute("UPDATE contracts SET end_date = ? WHERE id = ?", (new_end_date, contract_id))
    db.commit()
    return RedirectResponse("/", status_code=302)


@app.post("/import-csv", response_class=RedirectResponse)
async def import_csv(file: UploadFile = File(...), db: sqlite3.Connection = Depends(get_db)):
    content = await file.read()
    reader = csv.DictReader(io.StringIO(content.decode("utf-8")))
    count = 0
    for row in reader:
        try:
            db.execute(
                """INSERT OR IGNORE INTO contracts (vendor_name, contract_name, category, end_date, amount, currency, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (row.get("vendor_name", ""), row.get("contract_name", ""), row.get("category", "Other"),
                 row.get("end_date", ""), float(row.get("amount", 0) or 0),
                 row.get("currency", "USD"), row.get("notes", ""))
            )
            count += 1
        except Exception:
            continue
    db.commit()
    return RedirectResponse(f"/?imported={count}", status_code=302)


@app.get("/export-csv")
async def export_csv(db: sqlite3.Connection = Depends(get_db)):
    contracts = db.execute("SELECT * FROM contracts WHERE status = 'active'").fetchall()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["vendor_name", "contract_name", "category", "start_date", "end_date",
                     "amount", "currency", "billing_cycle", "auto_renews", "notice_days", "owner_email", "notes"])
    for c in contracts:
        writer.writerow([c["vendor_name"], c["contract_name"], c["category"], c["start_date"],
                         c["end_date"], c["amount"], c["currency"], c["billing_cycle"],
                         c["auto_renews"], c["notice_days"], c["owner_email"], c["notes"]])
    output.seek(0)
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=contracts.csv"}
    )


@app.get("/api/contracts")
async def list_contracts(db: sqlite3.Connection = Depends(get_db)):
    rows = db.execute("SELECT * FROM contracts WHERE status = 'active' ORDER BY end_date").fetchall()
    return [dict(r) for r in rows]


@app.post("/api/trigger-alerts")
async def trigger_alerts():
    check_and_send_alerts()
    return {"success": True, "message": "Alert check completed"}


if __name__ == "__main__":
    init_db()
    t = threading.Thread(target=alert_scheduler, daemon=True)
    t.start()
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8001")))
