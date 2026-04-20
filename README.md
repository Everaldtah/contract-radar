# 📄 Contract Radar

> **Centralize all your vendor contracts and subscriptions. Get renewal alerts before it's too late.**

## Problem It Solves

SMBs typically manage 20–50+ vendor contracts, software subscriptions, and leases spread across email threads, shared drives, and sticky notes. Contracts auto-renew unexpectedly (costing thousands), or lapse without notice (causing service disruptions). Contract Radar gives you a single place to track every contract, with automated email alerts sent to the right person at the right time — 30, 60, or 90 days before expiry.

## Features

- **Contract registry** — Store all contracts with vendor, type, value, expiry, and owner
- **Smart alerts** — Per-contract configurable notice windows (default 30 days)
- **Dashboard** — Instant overview of active/expired contracts and MRR at risk
- **Renewal calendar** — Group upcoming renewals by month
- **Auto-renew tracking** — Flag contracts that need cancellation before expiry
- **Weekly summary email** — One-page digest of all upcoming renewals
- **Multi-type support** — Software, services, leases, NDA, employment contracts
- **Owner assignment** — Route alerts to the right team member per contract

## Tech Stack

- **Backend:** Python 3.11 + FastAPI
- **Email:** SMTP (works with Gmail, SendGrid, Mailgun)
- **Database:** In-memory (MVP) — swap to PostgreSQL for production

## Installation

```bash
git clone https://github.com/Everaldtah/contract-radar
cd contract-radar
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Usage

### Start the server
```bash
uvicorn main:app --reload --port 8002
```

### 1. Add a contract
```bash
curl -X POST http://localhost:8002/contracts \
  -H "X-API-Key: changeme" \
  -H "Content-Type: application/json" \
  -d '{
    "vendor_name": "Salesforce",
    "contract_type": "software",
    "annual_value": 36000,
    "expiry_date": "2025-09-30",
    "auto_renews": false,
    "renewal_notice_days": 60,
    "owner_email": "sales@company.com"
  }'
```

### 2. View dashboard
```bash
curl http://localhost:8002/dashboard -H "X-API-Key: changeme"
```

### 3. Get contracts expiring soon
```bash
curl "http://localhost:8002/contracts?expiring_within_days=30" \
  -H "X-API-Key: changeme"
```

### 4. Trigger expiry alerts
```bash
curl -X POST http://localhost:8002/alerts/check \
  -H "X-API-Key: changeme" \
  -H "Content-Type: application/json" \
  -d '{"alert_email": "ops@company.com", "default_notice_days": 30}'
```

### 5. Get renewal calendar
```bash
curl "http://localhost:8002/contracts/report/calendar?months_ahead=3" \
  -H "X-API-Key: changeme"
```

### 6. Seed demo data
```bash
python seed_demo.py
```

### API Docs
`http://localhost:8002/docs`

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/contracts` | Add a contract |
| GET | `/contracts` | List all (with filters) |
| GET | `/contracts/{id}` | Get a contract |
| PATCH | `/contracts/{id}` | Update a contract |
| DELETE | `/contracts/{id}` | Remove a contract |
| GET | `/dashboard` | Overview stats |
| GET | `/contracts/report/calendar` | Renewal calendar by month |
| POST | `/alerts/check` | Send expiry alerts now |
| POST | `/alerts/summary` | Send weekly summary email |

## Monetization Model

| Plan | Price | Features |
|------|-------|----------|
| Free | $0 | Up to 10 contracts, manual alerts |
| Professional | $29/mo | 100 contracts, automated alerts, email reports |
| Business | $79/mo | Unlimited contracts, Slack integration, CSV export |
| Agency | $199/mo | Multi-company, white-label, API access |

**Target customers:** Operations managers, CFOs, and founders at 10–500 person companies. Especially valuable for companies with SaaS-heavy stacks or commercial leases.

**Go-to-market:** Cold email outreach to CFOs with subject line: "You're probably missing a contract renewal this quarter."

## License

MIT
