# Contract Radar 📡

> Contract expiry tracker that monitors your vendor and client agreements, extracts key dates from contract text, and sends automated renewal alerts — so critical contracts never slip through the cracks.

## The Problem

Small and mid-size businesses manage dozens of contracts (SaaS subscriptions, vendor agreements, client retainers, leases, NDAs) across email threads, Dropbox folders, and spreadsheets. Missing a contract renewal means either unexpected auto-charges, service disruptions, or lost leverage during renegotiation. Dedicated CLM (Contract Lifecycle Management) tools like Ironclad or DocuSign CLM cost $30K+/year.

## Features

- **Contract registry** — store all contracts with counterparty, dates, value, and renewal type
- **Automatic date extraction** — paste contract text and the parser extracts expiry and start dates using regex (no manual entry)
- **Multi-threshold alerts** — get emailed at 30, 14, and 7 days before expiry (configurable per contract)
- **Per-contract email routing** — different alerts for different people (legal team, finance, ops)
- **Visual urgency indicators** — color-coded dashboard (critical/expiring soon/watch/active)
- **Contract value tracking** — see total portfolio value and MRR at risk
- **Renewal management** — one-click renewal to extend any contract with a new end date
- **REST API** — integrate with your existing tools
- **Daily automated check** — runs every morning at 8am UTC

## Tech Stack

- **Python 3.11+** / FastAPI
- **SQLite** — zero-config local storage
- **APScheduler** — daily cron for expiry checks
- **Regex date extraction** — no paid AI/OCR services needed
- **SMTP** — works with any email provider

## Installation

```bash
git clone https://github.com/Everaldtah/contract-radar
cd contract-radar

python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# Edit .env with your SMTP credentials

python main.py
```

App runs at **http://localhost:8002**

## Usage

### Add a Contract Manually
Fill in the form on the dashboard — title, counterparty, and end date are required.

### Auto-Extract Dates from Contract Text
Paste contract text into the "Contract Text" field — the parser will extract start and end dates automatically using keyword and pattern matching.

### Reminder Schedule
Default reminders: **30 days**, **14 days**, **7 days** before expiry. Customize per contract by changing the "Reminder Days" field (comma-separated).

### API Examples

```bash
# Add a contract
curl -X POST http://localhost:8002/contracts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "AWS Annual Commitment",
    "counterparty": "Amazon Web Services",
    "end_date": "2025-01-31",
    "value": 48000,
    "renewal_type": "manual",
    "email_alerts": "devops@co.com,finance@co.com",
    "reminder_days": "60,30,14,7"
  }'

# List contracts expiring in next 90 days
curl http://localhost:8002/upcoming?days=90

# Extract dates from contract text
curl -X POST http://localhost:8002/extract-dates \
  -H "Content-Type: application/json" \
  -d '{"text": "This agreement shall terminate on December 31, 2025..."}'

# Trigger alert check manually
curl -X POST http://localhost:8002/alerts/run
```

## Date Extraction

The parser recognizes these formats:
- `January 15, 2025` / `Jan 15 2025`
- `2025-01-15` (ISO 8601)
- `01/15/2025`
- `15.01.2025`
- `15th day of January, 2025`

And finds dates near keywords like: *expires*, *termination date*, *effective date*, *valid through*, *end date*

## Monetization Model

- **Free**: Up to 10 contracts, email alerts
- **Starter** ($19/mo): Up to 100 contracts, PDF text extraction, multi-user
- **Business** ($49/mo): Unlimited contracts, PDF/DOCX upload, team roles, Google Drive integration, contract templates
- **Agency** ($129/mo): White-label, client portals, API access, Zapier integration, audit trail

**Target market**: Legal ops teams, procurement, startup founders, SMBs managing vendor relationships, real estate (lease tracking), and accounting firms managing client contracts.
