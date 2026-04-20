"""Email notifications for contract expiry alerts and weekly summaries."""

import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from datetime import datetime

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASS = os.getenv("SMTP_PASS", "")
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)


def _send(to: str, subject: str, html: str):
    if not SMTP_USER:
        print(f"[EMAIL] Would send to {to}: {subject}")
        return
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = SMTP_FROM
        msg["To"] = to
        msg.attach(MIMEText(html, "html"))
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.sendmail(SMTP_FROM, to, msg.as_string())
        print(f"[EMAIL] Sent: {subject} → {to}")
    except Exception as e:
        print(f"[EMAIL] Failed: {e}")


async def send_expiry_alert(contract: dict, recipient: str):
    if not recipient:
        print(f"[ALERT] No recipient for {contract['vendor_name']}")
        return

    days = contract["days_until_expiry"]
    urgency_color = "#ef4444" if days <= 7 else "#f97316" if days <= 30 else "#eab308"
    urgency_label = "URGENT" if days <= 7 else "UPCOMING"
    auto_label = "⚠️ AUTO-RENEWS" if contract.get("auto_renews") else "🔔 ACTION REQUIRED"
    value_str = f"${contract['annual_value']:,.2f}/{contract.get('currency','USD')} /year" if contract.get("annual_value") else "Not specified"

    html = f"""
    <html><body style="font-family:sans-serif;max-width:600px;margin:0 auto">
      <div style="background:{urgency_color};color:white;padding:16px;border-radius:8px 8px 0 0">
        <h2 style="margin:0">{urgency_label}: Contract Expiring in {days} Days</h2>
        <p style="margin:4px 0 0">{auto_label}</p>
      </div>
      <div style="border:1px solid #e5e7eb;border-top:none;padding:20px;border-radius:0 0 8px 8px">
        <table style="width:100%;border-collapse:collapse">
          <tr><td style="padding:8px 0;color:#6b7280">Vendor</td><td><strong>{contract['vendor_name']}</strong></td></tr>
          <tr><td style="padding:8px 0;color:#6b7280">Type</td><td>{contract.get('contract_type','—').title()}</td></tr>
          <tr><td style="padding:8px 0;color:#6b7280">Expires</td><td><strong style="color:{urgency_color}">{contract['expiry_date']} ({days} days)</strong></td></tr>
          <tr><td style="padding:8px 0;color:#6b7280">Annual Value</td><td>{value_str}</td></tr>
          <tr><td style="padding:8px 0;color:#6b7280">Auto-Renews</td><td>{'Yes — cancel by expiry date if unwanted' if contract.get('auto_renews') else 'No — must manually renew'}</td></tr>
          <tr><td style="padding:8px 0;color:#6b7280">Owner</td><td>{contract.get('owner_name','—')}</td></tr>
        </table>
        {f'<p style="background:#f9fafb;padding:12px;border-radius:4px;margin-top:16px"><em>{contract.get("description","")}</em></p>' if contract.get('description') else ''}
        {f'<p><strong>Notes:</strong> {contract.get("notes","")}</p>' if contract.get('notes') else ''}
        <hr style="margin:20px 0">
        <p style="color:#6b7280;font-size:12px">Sent by Contract Radar. Log in to your dashboard to update this contract or mark it as renewed.</p>
      </div>
    </body></html>
    """

    _send(recipient, f"⏰ Contract Expiry Alert: {contract['vendor_name']} in {days} days", html)


async def send_summary_report(contracts: list, recipient: str, name: str = "Team"):
    today = datetime.utcnow().strftime("%B %d, %Y")
    expiring_30 = [c for c in contracts if 0 <= c["days_until_expiry"] <= 30]
    expiring_90 = [c for c in contracts if 31 <= c["days_until_expiry"] <= 90]
    expired = [c for c in contracts if c["days_until_expiry"] < 0]

    def rows(items):
        return "".join(
            f"<tr><td style='padding:6px 8px'>{c['vendor_name']}</td>"
            f"<td style='padding:6px 8px'>{c['expiry_date']}</td>"
            f"<td style='padding:6px 8px'>{c['days_until_expiry']}d</td>"
            f"<td style='padding:6px 8px'>{'Auto' if c.get('auto_renews') else 'Manual'}</td>"
            f"<td style='padding:6px 8px'>${c['annual_value']:,.0f}' if c.get('annual_value') else '—'}</td></tr>"
            for c in items
        )

    table_style = "width:100%;border-collapse:collapse;margin:12px 0"
    th_style = "background:#f3f4f6;padding:8px;text-align:left;font-size:12px;color:#374151"

    html = f"""
    <html><body style="font-family:sans-serif;max-width:680px;margin:0 auto">
      <h2>📄 Contract Radar — Weekly Summary</h2>
      <p>Hi {name}, here's your contract renewal status as of {today}.</p>

      <h3 style="color:#ef4444">🚨 Expiring in 30 Days ({len(expiring_30)})</h3>
      {'<table style="' + table_style + '"><tr>' +
       f'<th style="{th_style}">Vendor</th><th style="{th_style}">Expiry</th><th style="{th_style}">Days</th>' +
       f'<th style="{th_style}">Renewal</th><th style="{th_style}">Value</th></tr>' +
       rows(expiring_30) + '</table>' if expiring_30 else '<p style="color:#6b7280">None</p>'}

      <h3 style="color:#f97316">⚠️ Expiring in 31–90 Days ({len(expiring_90)})</h3>
      {'<table style="' + table_style + '"><tr>' +
       f'<th style="{th_style}">Vendor</th><th style="{th_style}">Expiry</th><th style="{th_style}">Days</th>' +
       f'<th style="{th_style}">Renewal</th><th style="{th_style}">Value</th></tr>' +
       rows(expiring_90) + '</table>' if expiring_90 else '<p style="color:#6b7280">None</p>'}

      <p style="color:#6b7280;font-size:12px;margin-top:32px">Contract Radar — keeping your renewals under control.</p>
    </body></html>
    """

    _send(recipient, f"📄 Contract Radar Weekly Summary — {today}", html)
