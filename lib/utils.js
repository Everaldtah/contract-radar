export function getDaysUntilExpiry(endDate) {
  if (!endDate) return null;
  const end = new Date(endDate);
  const now = new Date();
  now.setHours(0, 0, 0, 0);
  end.setHours(0, 0, 0, 0);
  return Math.round((end - now) / (1000 * 60 * 60 * 24));
}

export function formatCurrency(value) {
  return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 0 }).format(value);
}

export function getRiskColor(days) {
  if (days === null) return 'gray';
  if (days < 0) return 'red';
  if (days <= 14) return 'red';
  if (days <= 30) return 'yellow';
  if (days <= 60) return 'orange';
  return 'green';
}
