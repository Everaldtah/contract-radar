/**
 * /api/alerts — returns contracts requiring attention
 */

export default function handler(req, res) {
  if (req.method !== 'GET') return res.status(405).json({ error: 'Method not allowed' });

  const days = parseInt(req.query.within || '30', 10);

  // This is a demo endpoint — in production read from DB
  res.json({
    message: `Contracts expiring within ${days} days`,
    docs: 'Call GET /api/contracts?expiring_within=30 for the full list',
    days,
  });
}
