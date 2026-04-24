import { getDaysUntilExpiry } from '../../../lib/utils';

// Reference same in-memory store
// In production this would be a DB query
let contracts = require('../contracts').default;

export default function handler(req, res) {
  const { id } = req.query;

  if (req.method === 'GET') {
    // Re-import to get the current store (works for demo purposes)
    const contract = contracts?.find?.(c => c.id === id);
    if (!contract) return res.status(404).json({ error: 'Contract not found' });
    return res.json({
      ...contract,
      daysUntilExpiry: contract.endDate ? getDaysUntilExpiry(contract.endDate) : null,
    });
  }

  if (req.method === 'DELETE') {
    return res.json({ message: 'Contract deleted', id });
  }

  if (req.method === 'PATCH') {
    return res.json({ message: 'Contract updated', id, updates: req.body });
  }

  return res.status(405).json({ error: 'Method not allowed' });
}
