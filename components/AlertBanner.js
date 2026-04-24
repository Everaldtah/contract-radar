export default function AlertBanner({ count, contracts }) {
  return (
    <div className="bg-yellow-50 border border-yellow-200 rounded-xl p-4 mb-6">
      <div className="flex items-start gap-3">
        <span className="text-2xl">⚠️</span>
        <div>
          <p className="font-semibold text-yellow-800">
            {count} contract{count > 1 ? 's' : ''} expiring within 30 days
          </p>
          <ul className="mt-1 text-sm text-yellow-700 space-y-0.5">
            {contracts.slice(0, 3).map(c => (
              <li key={c.id}>
                • <strong>{c.title}</strong> — {c.daysUntilExpiry === 0 ? 'TODAY' : `${c.daysUntilExpiry}d left`}
                {c.vendor ? ` (${c.vendor})` : ''}
              </li>
            ))}
            {contracts.length > 3 && <li>• ...and {contracts.length - 3} more</li>}
          </ul>
        </div>
      </div>
    </div>
  );
}
