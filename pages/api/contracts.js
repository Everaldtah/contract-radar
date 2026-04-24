/**
 * /api/contracts — CRUD for contracts.
 * In production, replace the in-memory store with a real DB.
 */

import { parseContractText } from '../../lib/contractParser';
import { getDaysUntilExpiry } from '../../lib/utils';

// In-memory store (persists per server process)
let contracts = [
  // Seed data for demo
  {
    id: 'demo_1',
    title: 'AWS Enterprise Agreement',
    vendor: 'Amazon Web Services',
    startDate: '2024-01-01',
    endDate: '2026-06-30',
    renewalNotice: 90,
    contractValue: 48000,
    autoRenews: true,
    status: 'active',
    notes: 'Annual committed spend. Auto-renews unless cancelled 90 days before.',
    tags: ['cloud', 'infrastructure'],
    createdAt: new Date().toISOString(),
  },
  {
    id: 'demo_2',
    title: 'Salesforce CRM License',
    vendor: 'Salesforce',
    startDate: '2025-05-01',
    endDate: '2026-05-31',
    renewalNotice: 60,
    contractValue: 24000,
    autoRenews: false,
    status: 'active',
    notes: '20 seats at $100/seat/month',
    tags: ['crm', 'sales'],
    createdAt: new Date().toISOString(),
  },
  {
    id: 'demo_3',
    title: 'Office Lease — 4th Floor',
    vendor: 'Metropolitan Properties',
    startDate: '2022-06-01',
    endDate: '2026-05-31',
    renewalNotice: 180,
    contractValue: 120000,
    autoRenews: false,
    status: 'active',
    notes: '$10,000/month. Must notify 6 months before expiry.',
    tags: ['real-estate', 'lease'],
    createdAt: new Date().toISOString(),
  },
];

let idCounter = 100;

function withDaysUntilExpiry(contract) {
  return {
    ...contract,
    daysUntilExpiry: contract.endDate ? getDaysUntilExpiry(contract.endDate) : null,
    renewalDeadline: contract.endDate && contract.renewalNotice
      ? getRenewalDeadline(contract.endDate, contract.renewalNotice)
      : null,
  };
}

function getRenewalDeadline(endDate, noticeDays) {
  const end = new Date(endDate);
  end.setDate(end.getDate() - noticeDays);
  return end.toISOString().split('T')[0];
}

export default function handler(req, res) {
  if (req.method === 'GET') {
    const { tag, vendor, expiring_within } = req.query;
    let result = contracts.map(withDaysUntilExpiry);

    if (tag) result = result.filter(c => c.tags?.includes(tag));
    if (vendor) result = result.filter(c => c.vendor?.toLowerCase().includes(vendor.toLowerCase()));
    if (expiring_within) {
      const days = parseInt(expiring_within, 10);
      result = result.filter(c => c.daysUntilExpiry !== null && c.daysUntilExpiry <= days && c.daysUntilExpiry >= 0);
    }

    return res.json({
      contracts: result.sort((a, b) => (a.daysUntilExpiry ?? 999) - (b.daysUntilExpiry ?? 999)),
      count: result.length,
      totalValue: result.reduce((acc, c) => acc + (parseFloat(c.contractValue) || 0), 0),
    });
  }

  if (req.method === 'POST') {
    const body = req.body;
    let parsed = {};

    // If raw_text is provided, extract dates/metadata
    if (body.raw_text) {
      parsed = parseContractText(body.raw_text);
    }

    const contract = {
      id: `contract_${++idCounter}`,
      title: body.title || parsed.title || 'Untitled Contract',
      vendor: body.vendor || parsed.vendor || '',
      startDate: body.startDate || parsed.startDate || null,
      endDate: body.endDate || parsed.endDate || null,
      renewalNotice: parseInt(body.renewalNotice || parsed.renewalNotice || '30', 10),
      contractValue: parseFloat(body.contractValue || parsed.contractValue || '0'),
      autoRenews: body.autoRenews === 'true' || body.autoRenews === true || parsed.autoRenews || false,
      status: 'active',
      notes: body.notes || parsed.notes || '',
      tags: Array.isArray(body.tags) ? body.tags : (body.tags ? body.tags.split(',').map(t => t.trim()) : []),
      raw_text: body.raw_text || '',
      createdAt: new Date().toISOString(),
    };

    contracts.push(contract);
    return res.status(201).json(withDaysUntilExpiry(contract));
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
