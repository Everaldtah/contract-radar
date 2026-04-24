# Contract Radar

**Never get auto-renewed into a contract you forgot about.** Contract Radar tracks all your vendor contracts, extracts key renewal dates, and sends alerts before you miss a deadline.

## The Problem

Freelancers and small agencies manage dozens of vendor contracts — SaaS subscriptions, office leases, service agreements, retainers. These are scattered across email threads, shared drives, and Notion pages. Companies get hit with surprise auto-renewals and miss opt-out windows, costing thousands. A single missed cancellation on an annual SaaS contract can cost $12,000+.

## What It Does

- **Dashboard** — all contracts at a glance with color-coded urgency (red = expiring soon)
- **Manual entry** — fill out a simple form with key dates and terms
- **Smart text parser** — paste raw contract text and auto-extract dates, vendor name, value, notice periods
- **Countdown timers** — days until expiry shown on every card
- **Renewal deadline calculator** — "you must decide by [date]" based on notice period
- **Alert banner** — immediate warning for contracts expiring within 30 days
- **REST API** — integrate with your existing workflows
- **Tagging system** — organize by category (cloud, lease, legal, etc.)

## Tech Stack

- **Framework**: Next.js 14 (React)
- **Styling**: Tailwind CSS
- **Parser**: Custom regex-based contract text extractor
- **Data**: In-memory (swap for PostgreSQL + Prisma)

## Installation

```bash
git clone https://github.com/Everaldtah/contract-radar.git
cd contract-radar
npm install
cp .env.example .env
npm run dev
```

Open http://localhost:3000

## Usage

### Web UI

1. Open the app and see pre-loaded demo contracts
2. Click **Manual Entry** to add a contract with specific dates
3. Click **Paste Text** to auto-parse a contract
4. Filter by "Expiring", "Active", or "Expired"
5. Delete contracts with the × button

### API

**List all contracts:**
```bash
curl http://localhost:3000/api/contracts
```

**Get contracts expiring within 30 days:**
```bash
curl "http://localhost:3000/api/contracts?expiring_within=30"
```

**Add a contract manually:**
```bash
curl -X POST http://localhost:3000/api/contracts \
  -H "Content-Type: application/json" \
  -d '{
    "title": "GitHub Teams Plan",
    "vendor": "GitHub",
    "startDate": "2025-01-01",
    "endDate": "2026-12-31",
    "renewalNotice": 30,
    "contractValue": 1188,
    "autoRenews": true,
    "tags": ["dev-tools", "saas"]
  }'
```

**Parse contract from raw text:**
```bash
curl -X POST http://localhost:3000/api/contracts \
  -H "Content-Type: application/json" \
  -d '{
    "raw_text": "Service Agreement between Acme Corp and Vendor Inc. Effective Date: January 1, 2025. Expiration: December 31, 2026. Total value: $24,000. Auto-renewal: 60 days written notice required."
  }'
```

## Contract Fields

| Field | Description |
|-------|-------------|
| title | Contract name |
| vendor | Vendor/supplier name |
| startDate | Contract start (YYYY-MM-DD) |
| endDate | Contract end (YYYY-MM-DD) |
| renewalNotice | Days of notice required to cancel/not-renew |
| contractValue | Annual or total contract value in USD |
| autoRenews | Whether the contract auto-renews |
| tags | Categories for filtering |
| notes | Free-text notes |

## Monetization Model

| Plan | Price | Features |
|------|-------|----------|
| Free | $0 | Up to 5 contracts, email alerts |
| Pro | $12/mo | Unlimited contracts, Slack alerts, PDF import |
| Team | $29/mo | 5 seats, shared workspace, audit log |
| Agency | $79/mo | Unlimited seats, client portals, API access |

**Target customers**: Freelancers, small agencies, operations managers, legal teams at startups.

**Unit economics**: The average freelancer manages 8–15 active contracts. Missing one auto-renewal = $500–$10,000 loss. This tool pays for itself in one saved cancellation.

## Roadmap

- [ ] PDF upload with text extraction (pdf-parse)
- [ ] Email digest — weekly contract health report
- [ ] Slack / Teams integration
- [ ] Calendar sync (Google Calendar reminders)
- [ ] Team sharing and permissions
- [ ] AI-powered contract summarization

## License

MIT
