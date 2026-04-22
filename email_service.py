import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from typing import List, Tuple

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
FROM_NAME = os.getenv("FROM_NAME", "Contract Radar")
DEFAULT_ALERT_EMAIL = os.getenv("DEFAULT_ALERT_EMAIL", "")


def _urgency_label(days_left: int) -> str:
    if days_left <= 7:
        return "CRITICAL"
    elif days_left <= 14:
        return "URGENT"
    elif days_left <= 30:
        return "ACTION REQUIRED"
    return "REMINDER"


def send_expiry_alerts(alerts: List[Tuple[dict, int]]):
    """Send expiry alert emails. alerts = list of (contract, days_left) tuples."""
    if not SMTP_USER or not SMTP_PASSWORD:
        for contract, days_left in alerts:
            print(f"[Alert Skipped] {_urgency_label(days_left)}: '{contract['title']}' expires in {days_left} days")
        return

    try:
        server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)

        for contract, days_left in alerts:
            recipients = []
            if contract.get("email_alerts"):
                recipients.extend([e.strip() for e in contract["email_alerts"].split(",")])
            if DEFAULT_ALERT_EMAIL and DEFAULT_ALERT_EMAIL not in recipients:
                recipients.append(DEFAULT_ALERT_EMAIL)
            if not recipients:
                print(f"[Alert] No recipients for contract '{contract['title']}'")
                continue

            urgency = _urgency_label(days_left)
            value_str = f" (${contract.get('value') or 0:,.0f} {contract.get('currency','USD')})" if contract.get("value") else ""

            html = f"""
            <html><body style='font-family:Arial,sans-serif;max-width:600px;margin:0 auto'>
            <div style='background:{"#e74c3c" if days_left <= 14 else "#e67e22"};color:white;padding:20px 28px;border-radius:8px 8px 0 0'>
                <h2 style='margin:0'>📡 Contract Expiry Alert — {urgency}</h2>
            </div>
            <div style='background:#fff;padding:24px 28px;border:1px solid #eee;border-radius:0 0 8px 8px'>
                <p style='font-size:16px'>The following contract <strong>expires in {days_left} day{"s" if days_left != 1 else ""}</strong>:</p>
                <table style='width:100%;border-collapse:collapse;margin:16px 0'>
                    <tr><td style='padding:8px;color:#666;width:160px'>Contract</td><td style='padding:8px;font-weight:bold'>{contract['title']}</td></tr>
                    <tr style='background:#f8f9fa'><td style='padding:8px;color:#666'>Counterparty</td><td style='padding:8px'>{contract['counterparty']}</td></tr>
                    <tr><td style='padding:8px;color:#666'>Expiry Date</td><td style='padding:8px;color:{"#e74c3c" if days_left <= 14 else "#e67e22"};font-weight:bold'>{contract['end_date']}</td></tr>
                    <tr style='background:#f8f9fa'><td style='padding:8px;color:#666'>Renewal Type</td><td style='padding:8px'>{contract.get('renewal_type','—').title()}</td></tr>
                    <tr><td style='padding:8px;color:#666'>Value</td><td style='padding:8px'>{value_str or '—'}</td></tr>
                </table>
                <p style='color:#666;font-size:14px'>{f"<strong>Notes:</strong> {contract['notes']}" if contract.get('notes') else ""}</p>
                <p style='margin-top:24px'>Please take action to {"renew or terminate" if contract.get("renewal_type") != "auto-renew" else "review auto-renewal terms for"} this contract before it expires.</p>
                <p style='color:#999;font-size:12px;margin-top:32px'>Powered by Contract Radar · <a href='{os.getenv("APP_URL","http://localhost:8002")}'>View Dashboard</a></p>
            </div>
            </body></html>"""

            msg = MIMEMultipart("alternative")
            msg["From"] = f"{FROM_NAME} <{SMTP_USER}>"
            msg["To"] = ", ".join(recipients)
            msg["Subject"] = f"📡 [{urgency}] Contract Expiry: '{contract['title']}' expires in {days_left} day{'s' if days_left != 1 else ''}"
            msg.attach(MIMEText(html, "html"))

            server.sendmail(SMTP_USER, recipients, msg.as_string())
            print(f"[Alert Sent] '{contract['title']}' → {recipients}")

        server.quit()
    except Exception as e:
        print(f"[Alert Error] {e}")
