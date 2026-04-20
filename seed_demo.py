"""
Seed demo data into Contract Radar for testing.
Run: python seed_demo.py (while server is running on port 8002)
"""

import requests
import json
from datetime import date, timedelta

BASE = "http://localhost:8002"
HEADERS = {"X-API-Key": "changeme", "Content-Type": "application/json"}

contracts = [
    {
        "vendor_name": "AWS",
        "contract_type": "software",
        "description": "Cloud infrastructure — EC2, S3, RDS",
        "annual_value": 48000,
        "expiry_date": (date.today() + timedelta(days=15)).isoformat(),
        "auto_renews": True,
        "renewal_notice_days": 30,
        "owner_email": "devops@company.com",
        "tags": ["cloud", "infrastructure"],
    },
    {
        "vendor_name": "Salesforce",
        "contract_type": "software",
        "description": "CRM platform — 25 seats",
        "annual_value": 36000,
        "expiry_date": (date.today() + timedelta(days=45)).isoformat(),
        "auto_renews": False,
        "renewal_notice_days": 60,
        "owner_email": "sales@company.com",
        "tags": ["crm", "sales"],
    },
    {
        "vendor_name": "Office Lease – 450 Park Ave",
        "contract_type": "lease",
        "description": "3rd floor office space, 4,000 sq ft",
        "annual_value": 120000,
        "expiry_date": (date.today() + timedelta(days=72)).isoformat(),
        "auto_renews": False,
        "renewal_notice_days": 90,
        "owner_email": "cfo@company.com",
        "tags": ["real-estate", "office"],
    },
    {
        "vendor_name": "Zendesk",
        "contract_type": "software",
        "description": "Customer support platform",
        "annual_value": 12000,
        "expiry_date": (date.today() + timedelta(days=180)).isoformat(),
        "auto_renews": True,
        "renewal_notice_days": 30,
        "owner_email": "support@company.com",
        "tags": ["support"],
    },
    {
        "vendor_name": "Legal Services – Wilson & Partners",
        "contract_type": "service",
        "description": "Annual retainer for IP and contract review",
        "annual_value": 24000,
        "expiry_date": (date.today() - timedelta(days=5)).isoformat(),  # already expired
        "auto_renews": False,
        "renewal_notice_days": 30,
        "owner_email": "legal@company.com",
        "tags": ["legal"],
    },
]

print("Seeding demo contracts...")
for c in contracts:
    r = requests.post(f"{BASE}/contracts", headers=HEADERS, json=c)
    if r.status_code == 200:
        print(f"  ✓ {c['vendor_name']} (expires {c['expiry_date']})")
    else:
        print(f"  ✗ {c['vendor_name']}: {r.text}")

print("\nDashboard:")
r = requests.get(f"{BASE}/dashboard", headers=HEADERS)
print(json.dumps(r.json(), indent=2))
