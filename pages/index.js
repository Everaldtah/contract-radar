import { useState, useEffect } from 'react';
import Head from 'next/head';
import ContractCard from '../components/ContractCard';
import UploadForm from '../components/UploadForm';
import AlertBanner from '../components/AlertBanner';

export default function Home() {
  const [contracts, setContracts] = useState([]);
  const [filter, setFilter] = useState('all');
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState([]);

  useEffect(() => {
    fetchContracts();
  }, []);

  async function fetchContracts() {
    setLoading(true);
    try {
      const res = await fetch('/api/contracts');
      const data = await res.json();
      setContracts(data.contracts || []);
      setAlerts((data.contracts || []).filter(c => {
        const days = c.daysUntilExpiry;
        return days !== null && days <= 30 && days >= 0;
      }));
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  }

  const filtered = contracts.filter(c => {
    if (filter === 'expiring') return c.daysUntilExpiry !== null && c.daysUntilExpiry <= 30;
    if (filter === 'expired') return c.daysUntilExpiry !== null && c.daysUntilExpiry < 0;
    if (filter === 'active') return c.daysUntilExpiry === null || c.daysUntilExpiry > 30;
    return true;
  });

  const stats = {
    total: contracts.length,
    expiringSoon: contracts.filter(c => c.daysUntilExpiry !== null && c.daysUntilExpiry <= 30 && c.daysUntilExpiry >= 0).length,
    expired: contracts.filter(c => c.daysUntilExpiry !== null && c.daysUntilExpiry < 0).length,
    totalValue: contracts.reduce((acc, c) => acc + (parseFloat(c.contractValue) || 0), 0),
  };

  return (
    <>
      <Head>
        <title>Contract Radar — Never Miss a Renewal</title>
        <meta name="description" content="Track contract deadlines, renewals, and expirations" />
      </Head>

      <div className="min-h-screen bg-gray-50">
        <header className="bg-indigo-700 text-white shadow">
          <div className="max-w-6xl mx-auto px-4 py-5 flex items-center justify-between">
            <div>
              <h1 className="text-2xl font-bold">📡 Contract Radar</h1>
              <p className="text-indigo-200 text-sm">Never miss a renewal deadline</p>
            </div>
            <a href="/api-docs" className="text-indigo-200 hover:text-white text-sm">API Docs →</a>
          </div>
        </header>

        <main className="max-w-6xl mx-auto px-4 py-8">
          {alerts.length > 0 && (
            <AlertBanner count={alerts.length} contracts={alerts} />
          )}

          {/* Stats */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
            {[
              { label: 'Total Contracts', value: stats.total, color: 'indigo' },
              { label: 'Expiring Soon', value: stats.expiringSoon, color: 'yellow' },
              { label: 'Expired', value: stats.expired, color: 'red' },
              { label: 'Total Value', value: `$${stats.totalValue.toLocaleString()}`, color: 'green' },
            ].map(s => (
              <div key={s.label} className="bg-white rounded-xl shadow-sm p-5 border border-gray-100">
                <p className="text-gray-500 text-sm">{s.label}</p>
                <p className={`text-3xl font-bold text-${s.color}-600 mt-1`}>{s.value}</p>
              </div>
            ))}
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
            {/* Upload form */}
            <div className="lg:col-span-1">
              <UploadForm onSuccess={fetchContracts} />
            </div>

            {/* Contract list */}
            <div className="lg:col-span-2">
              <div className="flex items-center justify-between mb-4">
                <h2 className="text-lg font-semibold text-gray-800">Contracts</h2>
                <div className="flex gap-2">
                  {['all', 'expiring', 'active', 'expired'].map(f => (
                    <button
                      key={f}
                      onClick={() => setFilter(f)}
                      className={`px-3 py-1 rounded-full text-sm font-medium transition ${
                        filter === f
                          ? 'bg-indigo-600 text-white'
                          : 'bg-white text-gray-600 border border-gray-200 hover:border-indigo-400'
                      }`}
                    >
                      {f.charAt(0).toUpperCase() + f.slice(1)}
                    </button>
                  ))}
                </div>
              </div>

              {loading ? (
                <div className="text-center py-12 text-gray-400">Loading contracts...</div>
              ) : filtered.length === 0 ? (
                <div className="text-center py-12 text-gray-400 bg-white rounded-xl border border-dashed border-gray-200">
                  <p className="text-4xl mb-3">📄</p>
                  <p>No contracts yet. Add your first contract using the form.</p>
                </div>
              ) : (
                <div className="space-y-3">
                  {filtered
                    .sort((a, b) => (a.daysUntilExpiry ?? 999) - (b.daysUntilExpiry ?? 999))
                    .map(contract => (
                      <ContractCard
                        key={contract.id}
                        contract={contract}
                        onDelete={fetchContracts}
                      />
                    ))}
                </div>
              )}
            </div>
          </div>
        </main>
      </div>
    </>
  );
}
