import { formatCurrency, getRiskColor } from '../lib/utils';

const URGENCY_CONFIG = {
  red: { bg: 'bg-red-50', border: 'border-red-200', badge: 'bg-red-100 text-red-700', dot: 'bg-red-500' },
  yellow: { bg: 'bg-yellow-50', border: 'border-yellow-200', badge: 'bg-yellow-100 text-yellow-700', dot: 'bg-yellow-500' },
  orange: { bg: 'bg-orange-50', border: 'border-orange-200', badge: 'bg-orange-100 text-orange-700', dot: 'bg-orange-500' },
  green: { bg: 'bg-white', border: 'border-gray-100', badge: 'bg-green-100 text-green-700', dot: 'bg-green-500' },
  gray: { bg: 'bg-white', border: 'border-gray-100', badge: 'bg-gray-100 text-gray-600', dot: 'bg-gray-400' },
};

export default function ContractCard({ contract, onDelete }) {
  const days = contract.daysUntilExpiry;
  const colorKey = getRiskColor(days);
  const config = URGENCY_CONFIG[colorKey] || URGENCY_CONFIG.gray;

  function getBadgeLabel() {
    if (days === null) return 'No expiry';
    if (days < 0) return `Expired ${Math.abs(days)}d ago`;
    if (days === 0) return 'Expires TODAY';
    return `${days}d left`;
  }

  async function handleDelete() {
    if (!confirm(`Delete "${contract.title}"?`)) return;
    await fetch(`/api/contracts/${contract.id}`, { method: 'DELETE' });
    onDelete?.();
  }

  return (
    <div className={`rounded-xl border p-5 ${config.bg} ${config.border} transition hover:shadow-md`}>
      <div className="flex items-start justify-between gap-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <span className={`inline-block w-2.5 h-2.5 rounded-full flex-shrink-0 ${config.dot}`}></span>
            <h3 className="font-semibold text-gray-800 truncate">{contract.title}</h3>
          </div>
          <p className="text-gray-500 text-sm">{contract.vendor || 'Unknown vendor'}</p>
        </div>

        <div className="flex items-center gap-2 flex-shrink-0">
          <span className={`text-xs font-bold px-2.5 py-1 rounded-full ${config.badge}`}>
            {getBadgeLabel()}
          </span>
          <button
            onClick={handleDelete}
            className="text-gray-300 hover:text-red-400 transition text-lg leading-none"
            title="Delete contract"
          >
            ×
          </button>
        </div>
      </div>

      <div className="mt-3 grid grid-cols-2 sm:grid-cols-4 gap-3 text-sm">
        <div>
          <p className="text-gray-400 text-xs">Value</p>
          <p className="font-medium text-gray-700">
            {contract.contractValue ? formatCurrency(contract.contractValue) : '—'}
          </p>
        </div>
        <div>
          <p className="text-gray-400 text-xs">End Date</p>
          <p className="font-medium text-gray-700">{contract.endDate || '—'}</p>
        </div>
        <div>
          <p className="text-gray-400 text-xs">Notice Period</p>
          <p className="font-medium text-gray-700">
            {contract.renewalNotice ? `${contract.renewalNotice} days` : '—'}
          </p>
        </div>
        <div>
          <p className="text-gray-400 text-xs">Auto-renews</p>
          <p className="font-medium text-gray-700">{contract.autoRenews ? '✅ Yes' : '❌ No'}</p>
        </div>
      </div>

      {contract.renewalDeadline && days !== null && days >= 0 && (
        <p className="mt-3 text-xs text-yellow-700 bg-yellow-100 px-3 py-1.5 rounded-lg">
          ⚠️ Renewal decision needed by <strong>{contract.renewalDeadline}</strong> ({contract.renewalNotice}d notice)
        </p>
      )}

      {contract.notes && (
        <p className="mt-2 text-xs text-gray-500 truncate">{contract.notes}</p>
      )}

      {contract.tags?.length > 0 && (
        <div className="mt-2 flex gap-1 flex-wrap">
          {contract.tags.map(tag => (
            <span key={tag} className="text-xs px-2 py-0.5 bg-indigo-50 text-indigo-600 rounded-full">{tag}</span>
          ))}
        </div>
      )}
    </div>
  );
}
