# Contract Radar

> Never get blindsided by a contract renewal again. Track all your vendor contracts and SaaS subscriptions with automatic expiry alerts.

---

## The Problem

Small and mid-size businesses silently waste thousands of dollars each year renewing contracts they meant to cancel — or worse, letting critical vendor agreements lapse unexpectedly. Spreadsheets get outdated. Reminders get missed.

**Contract Radar** is a lightweight contract lifecycle tracker that alerts you 60, 30, 14, 7, and 1 day(s) before any contract expires — so you can decide to renew, renegotiate, or cancel.

---

## Features

- **Contract dashboard** — All contracts sorted by urgency (expiring soonest first)
- **Automatic email alerts** — Configurable alert windows (60, 30, 14, 7, 1 days)
- **Auto-renewal tracking** — Flag contracts that auto-renew so you don't miss cancellation windows
- **CSV import/export** — Bulk-load existing contracts from spreadsheets
- **Category organization** — SaaS, Legal, HR, Infrastructure, etc.
- **Renewal tracking** — One-click renewal with new date
- **Annual value tracking** — Know your total vendor spend at a glance

---

## Tech Stack

- **Backend**: Python 3.11+ / FastAPI
- **Database**: SQLite
- **Templating**: Jinja2
- **Email**: Python `smtplib` (SMTP)
- **Scheduling**: Background thread

---

## Installation

```bash
git clone https://github.com/Everaldtah/contract-radar.git
cd contract-radar

python -m venv venv
source venv/bin/activate

pip install -r requirements.txt

cp .env.example .env
# Edit .env with your alert email and SMTP settings

python main.py
```

Open http://localhost:8001

### Quick Start with Sample Data

```bash
# Import sample contracts via the UI
# Click "Import CSV" and upload sample_contracts.csv
```

---

## CSV Import Format

```csv
vendor_name,contract_name,category,end_date,amount,currency,notes
Salesforce,CRM Enterprise,SaaS,2026-09-30,36000,USD,Auto-renews 60 days notice
AWS,Cloud Infrastructure,Cloud Infrastructure,2026-12-31,48000,USD,Reserved instances
```

---

## Alert Configuration

Edit `.env`:
```
ALERT_DAYS=60,30,14,7,1     # Days before expiry to send alerts
ALERT_EMAIL=ops@company.com  # Who receives the alerts
```

---

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/` | Dashboard |
| POST | `/contracts` | Add contract |
| POST | `/contracts/{id}/renew` | Renew with new date |
| POST | `/contracts/{id}/delete` | Archive contract |
| GET | `/export-csv` | Export all contracts |
| POST | `/import-csv` | Import from CSV |
| GET | `/api/contracts` | JSON list |
| POST | `/api/trigger-alerts` | Manual alert check |

---

## Monetization Model

| Plan | Price | Features |
|------|-------|----------|
| **Free** | $0/mo | Up to 10 contracts |
| **Business** | $19/mo | Unlimited contracts, multi-user, Slack alerts |
| **Team** | $49/mo | Multiple workspaces, audit log, Jira integration |
| **Enterprise** | $149/mo | SSO, custom alerts, ERP integrations, SLA |

**ROI story**: A single accidentally auto-renewed $36k Salesforce contract pays for years of subscription.

---

## Traction Potential

- **Every company has this problem** — vendor contracts are universal
- **High switching cost** — once contracts are entered, users stay
- **Procurement teams** are the buyer: well-defined budget and clear ROI
- **Upsell path**: Start with 1 workspace, expand to multi-team, add integrations
