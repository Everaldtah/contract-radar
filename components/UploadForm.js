import { useState } from 'react';

export default function UploadForm({ onSuccess }) {
  const [mode, setMode] = useState('manual'); // 'manual' or 'paste'
  const [loading, setLoading] = useState(false);
  const [msg, setMsg] = useState(null);
  const [form, setForm] = useState({
    title: '', vendor: '', startDate: '', endDate: '',
    renewalNotice: 30, contractValue: '', autoRenews: false,
    notes: '', tags: '',
  });
  const [rawText, setRawText] = useState('');

  function update(field, value) {
    setForm(f => ({ ...f, [field]: value }));
  }

  async function handleManualSubmit(e) {
    e.preventDefault();
    setLoading(true);
    setMsg(null);
    try {
      const res = await fetch('/api/contracts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(form),
      });
      if (res.ok) {
        setMsg({ type: 'success', text: '✅ Contract added!' });
        setForm({ title: '', vendor: '', startDate: '', endDate: '', renewalNotice: 30, contractValue: '', autoRenews: false, notes: '', tags: '' });
        onSuccess?.();
      } else {
        const err = await res.json();
        setMsg({ type: 'error', text: `❌ ${err.error || 'Error saving contract'}` });
      }
    } catch (e) {
      setMsg({ type: 'error', text: '❌ Network error' });
    } finally {
      setLoading(false);
    }
  }

  async function handlePasteSubmit(e) {
    e.preventDefault();
    if (!rawText.trim()) return;
    setLoading(true);
    setMsg(null);
    try {
      const res = await fetch('/api/contracts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ raw_text: rawText }),
      });
      if (res.ok) {
        setMsg({ type: 'success', text: '✅ Contract parsed and added!' });
        setRawText('');
        onSuccess?.();
      } else {
        setMsg({ type: 'error', text: '❌ Could not parse contract text' });
      }
    } catch {
      setMsg({ type: 'error', text: '❌ Network error' });
    } finally {
      setLoading(false);
    }
  }

  const inputClass = "w-full px-3 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-indigo-400 focus:ring-1 focus:ring-indigo-400";
  const labelClass = "block text-xs font-semibold text-gray-500 mb-1";

  return (
    <div className="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
      <h2 className="text-lg font-semibold text-gray-800 mb-4">Add Contract</h2>

      <div className="flex gap-2 mb-5">
        {['manual', 'paste'].map(m => (
          <button
            key={m}
            onClick={() => setMode(m)}
            className={`flex-1 py-2 text-sm font-medium rounded-lg transition ${
              mode === m ? 'bg-indigo-600 text-white' : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
            }`}
          >
            {m === 'manual' ? '📝 Manual Entry' : '📋 Paste Text'}
          </button>
        ))}
      </div>

      {mode === 'manual' ? (
        <form onSubmit={handleManualSubmit} className="space-y-3">
          <div>
            <label className={labelClass}>Contract Title *</label>
            <input required className={inputClass} value={form.title} onChange={e => update('title', e.target.value)} placeholder="AWS Enterprise Agreement" />
          </div>
          <div>
            <label className={labelClass}>Vendor</label>
            <input className={inputClass} value={form.vendor} onChange={e => update('vendor', e.target.value)} placeholder="Amazon Web Services" />
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass}>Start Date</label>
              <input type="date" className={inputClass} value={form.startDate} onChange={e => update('startDate', e.target.value)} />
            </div>
            <div>
              <label className={labelClass}>End Date</label>
              <input type="date" className={inputClass} value={form.endDate} onChange={e => update('endDate', e.target.value)} />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div>
              <label className={labelClass}>Contract Value ($)</label>
              <input type="number" className={inputClass} value={form.contractValue} onChange={e => update('contractValue', e.target.value)} placeholder="48000" />
            </div>
            <div>
              <label className={labelClass}>Notice Period (days)</label>
              <input type="number" className={inputClass} value={form.renewalNotice} onChange={e => update('renewalNotice', e.target.value)} />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <input type="checkbox" id="autoRenews" checked={form.autoRenews} onChange={e => update('autoRenews', e.target.checked)} className="rounded" />
            <label htmlFor="autoRenews" className="text-sm text-gray-600">Auto-renews</label>
          </div>
          <div>
            <label className={labelClass}>Tags (comma-separated)</label>
            <input className={inputClass} value={form.tags} onChange={e => update('tags', e.target.value)} placeholder="cloud, saas, critical" />
          </div>
          <div>
            <label className={labelClass}>Notes</label>
            <textarea className={inputClass + " h-20 resize-none"} value={form.notes} onChange={e => update('notes', e.target.value)} placeholder="Key terms, contacts, payment info..." />
          </div>
          <button type="submit" disabled={loading} className="w-full py-2.5 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 transition">
            {loading ? 'Saving...' : 'Add Contract'}
          </button>
        </form>
      ) : (
        <form onSubmit={handlePasteSubmit} className="space-y-3">
          <p className="text-sm text-gray-500">Paste contract text and we'll extract the key dates automatically.</p>
          <textarea
            className={inputClass + " h-48 resize-y font-mono text-xs"}
            value={rawText}
            onChange={e => setRawText(e.target.value)}
            placeholder={`Service Agreement

Between: Acme Corp (Customer) and Vendor Inc.
Effective Date: January 1, 2025
Expiration Date: December 31, 2026

Total Contract Value: $24,000

Auto-renewal: This agreement automatically renews unless either party provides 60 days written notice prior to the expiration date.`}
          />
          <button type="submit" disabled={loading || !rawText.trim()} className="w-full py-2.5 bg-indigo-600 text-white rounded-lg font-medium hover:bg-indigo-700 disabled:opacity-50 transition">
            {loading ? 'Parsing...' : 'Parse & Add Contract'}
          </button>
        </form>
      )}

      {msg && (
        <div className={`mt-3 p-3 rounded-lg text-sm ${msg.type === 'success' ? 'bg-green-50 text-green-700' : 'bg-red-50 text-red-700'}`}>
          {msg.text}
        </div>
      )}
    </div>
  );
}
