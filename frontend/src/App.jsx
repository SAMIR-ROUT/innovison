import { useState, useEffect, useCallback } from 'react';
import './App.css';

// ── env vars (Vite exposes VITE_* vars at build time) ──────────────────────
const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const API_KEY = import.meta.env.VITE_API_KEY || '';

// ── money formatter – Indian locale (₹1,20,000) ───────────────────────────
function formatINR(value) {
  const num = parseFloat(value);
  if (isNaN(num)) return '₹—';
  return '₹' + num.toLocaleString('en-IN', { minimumFractionDigits: 0, maximumFractionDigits: 2 });
}

// ── date formatter ─────────────────────────────────────────────────────────
function formatDate(iso) {
  if (!iso) return '—';
  const d = new Date(iso);
  if (isNaN(d.getTime())) return iso;
  return d.toLocaleString('en-IN', { dateStyle: 'medium', timeStyle: 'short' });
}

// ── generic API helper ─────────────────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const url = `${API_URL}${path}`;
  const headers = { 'Content-Type': 'application/json', ...options.headers };
  if (options.requireAuth) {
    headers['X-API-Key'] = API_KEY;
  }
  delete options.requireAuth;

  const res = await fetch(url, { ...options, headers });
  const data = await res.json();
  if (!res.ok) {
    // Backend error shape: { error: true, message: "...", status_code: N }
    const msg = data?.message || `HTTP ${res.status}`;
    throw Object.assign(new Error(msg), { status: res.status, data });
  }
  return data;
}

// ── HistoryPanel ───────────────────────────────────────────────────────────
function HistoryPanel({ sponsor, onClose }) {
  const [entries, setEntries] = useState(null); // null = loading
  const [error, setError] = useState('');

  useEffect(() => {
    let cancelled = false;
    apiFetch(`/sponsors/${sponsor.id}/history`)
      .then((data) => { if (!cancelled) setEntries(data); })
      .catch((e) => { if (!cancelled) setError(e.message); });
    return () => { cancelled = true; };
  }, [sponsor.id]);

  return (
    <div
      style={{
        border: '1px solid #c8d8ff',
        borderRadius: '8px',
        padding: '12px',
        marginBottom: '12px',
        backgroundColor: '#f8f9ff',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <h3 style={{ margin: 0, fontSize: '16px' }}>History — {sponsor.name}</h3>
        <button
          type="button"
          onClick={onClose}
          style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '18px', color: '#666' }}
          aria-label="Close history"
        >
          ✕
        </button>
      </div>

      {!entries && !error && <p style={{ color: '#666', fontSize: '14px' }}>Loading…</p>}
      {error && <p style={{ color: '#c00', fontSize: '14px' }}>Error: {error}</p>}

      {entries && entries.length === 0 && (
        <p style={{ color: '#888', fontSize: '14px' }}>No changes recorded yet.</p>
      )}

      {entries && entries.length > 0 && (
        <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
          <thead>
            <tr style={{ borderBottom: '1px solid #dde' }}>
              <th style={{ textAlign: 'left', padding: '5px 8px' }}>Date</th>
              <th style={{ textAlign: 'left', padding: '5px 8px' }}>Old</th>
              <th style={{ textAlign: 'left', padding: '5px 8px' }}>New</th>
              <th style={{ textAlign: 'left', padding: '5px 8px' }}>Note</th>
            </tr>
          </thead>
          <tbody>
            {entries.map((h) => (
              <tr key={h.id} style={{ borderBottom: '1px solid #eef' }}>
                <td style={{ padding: '5px 8px', whiteSpace: 'nowrap' }}>{formatDate(h.changed_at)}</td>
                <td style={{ padding: '5px 8px' }}>{formatINR(h.old_commitment)}</td>
                <td style={{ padding: '5px 8px' }}>{formatINR(h.new_commitment)}</td>
                <td style={{ padding: '5px 8px', color: '#555' }}>{h.note || '—'}</td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}

// ── AddSponsorForm ─────────────────────────────────────────────────────────
function AddSponsorForm({ onAdded }) {
  const [name, setName] = useState('');
  const [original, setOriginal] = useState('');
  const [current, setCurrent] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    // Client-side validation
    if (!name.trim()) {
      setError('Sponsor name cannot be empty.');
      return;
    }
    const orig = parseFloat(original);
    const curr = parseFloat(current);
    if (isNaN(orig) || orig <= 0) {
      setError('Original commitment must be a positive number.');
      return;
    }
    if (isNaN(curr) || curr <= 0) {
      setError('Current commitment must be a positive number.');
      return;
    }

    setSubmitting(true);
    try {
      const created = await apiFetch('/sponsors', {
        method: 'POST',
        requireAuth: true,
        body: JSON.stringify({
          name: name.trim(),
          original_commitment: orig,
          current_commitment: curr,
        }),
      });
      setName('');
      setOriginal('');
      setCurrent('');
      onAdded(created);
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '12px', marginBottom: '12px' }}>
      <h2 style={{ margin: '0 0 10px 0', fontSize: '18px' }}>Add Sponsor</h2>
      <form onSubmit={handleSubmit} noValidate>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="Sponsor name"
            value={name}
            onChange={(e) => setName(e.target.value)}
            style={{ flex: '2 1 160px', padding: '7px 10px', borderRadius: '5px', border: '1px solid #ccc' }}
            disabled={submitting}
          />
          <input
            type="number"
            placeholder="Original commitment (₹)"
            value={original}
            onChange={(e) => setOriginal(e.target.value)}
            min="1"
            style={{ flex: '1 1 160px', padding: '7px 10px', borderRadius: '5px', border: '1px solid #ccc' }}
            disabled={submitting}
          />
          <input
            type="number"
            placeholder="Current commitment (₹)"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            min="1"
            style={{ flex: '1 1 160px', padding: '7px 10px', borderRadius: '5px', border: '1px solid #ccc' }}
            disabled={submitting}
          />
          <button
            type="submit"
            disabled={submitting}
            style={{
              backgroundColor: submitting ? '#aaa' : '#007bff',
              color: '#fff',
              border: 'none',
              padding: '7px 16px',
              borderRadius: '5px',
              cursor: submitting ? 'not-allowed' : 'pointer',
            }}
          >
            {submitting ? 'Adding…' : 'Add'}
          </button>
        </div>
        {error && <p style={{ color: '#c00', margin: '6px 0 0', fontSize: '14px' }}>{error}</p>}
      </form>
    </div>
  );
}

// ── UpdateForm ─────────────────────────────────────────────────────────────
function UpdateForm({ sponsor, onUpdated, onCancel }) {
  const [current, setCurrent] = useState(String(parseFloat(sponsor.current_commitment)));
  const [note, setNote] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');

    const curr = parseFloat(current);
    if (isNaN(curr) || curr <= 0) {
      setError('Commitment must be a positive number.');
      return;
    }
    if (note.trim() === '' && note !== '') {
      // note is optional; but if supplied it must not be whitespace-only
      setError('Note cannot be blank spaces only. Leave it empty or write something.');
      return;
    }

    setSubmitting(true);
    try {
      const body = { current_commitment: curr };
      if (note.trim()) body.note = note.trim();

      const updated = await apiFetch(`/sponsors/${sponsor.id}`, {
        method: 'PATCH',
        requireAuth: true,
        body: JSON.stringify(body),
      });
      onUpdated(updated);
    } catch (e) {
      setError(e.message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div
      style={{
        border: '1px solid #e0a800',
        backgroundColor: '#fff9e6',
        borderRadius: '8px',
        padding: '12px',
        marginBottom: '12px',
      }}
    >
      <h3 style={{ margin: '0 0 8px 0', fontSize: '16px' }}>Update — {sponsor.name}</h3>
      <p style={{ margin: '0 0 8px 0', fontSize: '14px', color: '#555' }}>
        Current: {formatINR(sponsor.current_commitment)}
      </p>
      <form onSubmit={handleSubmit} noValidate>
        <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
          <input
            type="number"
            placeholder="New commitment (₹)"
            value={current}
            onChange={(e) => setCurrent(e.target.value)}
            min="1"
            style={{ flex: '1 1 160px', padding: '7px 10px', borderRadius: '5px', border: '1px solid #ccc' }}
            disabled={submitting}
          />
          <input
            type="text"
            placeholder="Note (optional)"
            value={note}
            onChange={(e) => setNote(e.target.value)}
            style={{ flex: '2 1 180px', padding: '7px 10px', borderRadius: '5px', border: '1px solid #ccc' }}
            disabled={submitting}
          />
          <button
            type="submit"
            disabled={submitting}
            style={{
              backgroundColor: submitting ? '#aaa' : '#28a745',
              color: '#fff',
              border: 'none',
              padding: '7px 14px',
              borderRadius: '5px',
              cursor: submitting ? 'not-allowed' : 'pointer',
            }}
          >
            {submitting ? 'Saving…' : 'Save'}
          </button>
          <button
            type="button"
            onClick={onCancel}
            disabled={submitting}
            style={{
              backgroundColor: '#6c757d',
              color: '#fff',
              border: 'none',
              padding: '7px 14px',
              borderRadius: '5px',
              cursor: submitting ? 'not-allowed' : 'pointer',
            }}
          >
            Cancel
          </button>
        </div>
        {error && <p style={{ color: '#c00', margin: '6px 0 0', fontSize: '14px' }}>{error}</p>}
      </form>
    </div>
  );
}

// ── App ────────────────────────────────────────────────────────────────────
function App() {
  const [sponsors, setSponsors] = useState([]);
  const [loading, setLoading] = useState(true);
  const [listError, setListError] = useState('');
  const [dbStatus, setDbStatus] = useState('');

  const [selectedSponsor, setSelectedSponsor] = useState(null); // for update form
  const [historyFor, setHistoryFor] = useState(null); // for history panel
  const [flashMsg, setFlashMsg] = useState('');

  // ── load sponsors ────────────────────────────────────────────────────────
  const loadSponsors = useCallback(() => {
    setLoading(true);
    setListError('');
    apiFetch('/sponsors')
      .then((data) => setSponsors(data))
      .catch((e) => setListError(e.message))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    let cancelled = false;
    // oxlint-disable-next-line react/set-state-in-effect -- async fetch pattern; setState only fires after promise resolves
    loadSponsors();
    // Also ping DB health
    apiFetch('/health/db')
      .then((d) => { if (!cancelled) setDbStatus(d.database === 'connected' ? '🟢 DB connected' : '🟡 DB status unknown'); })
      .catch(() => { if (!cancelled) setDbStatus('🔴 DB unreachable'); });
    return () => { cancelled = true; };
  }, [loadSponsors]);

  // ── flash helper ─────────────────────────────────────────────────────────
  function flash(msg) {
    setFlashMsg(msg);
    setTimeout(() => setFlashMsg(''), 4000);
  }

  // ── handlers ─────────────────────────────────────────────────────────────
  function handleSponsorClick(sponsor) {
    if (historyFor?.id === sponsor.id) {
      setHistoryFor(null);
    } else {
      setHistoryFor(sponsor);
      setSelectedSponsor(null);
    }
  }

  function handleEditClick(sponsor, e) {
    e.stopPropagation();
    setSelectedSponsor(sponsor);
    setHistoryFor(null);
  }

  function handleAdded(created) {
    setSponsors((prev) => [created, ...prev]);
    flash(`✅ ${created.name} added successfully.`);
  }

  function handleUpdated(updated) {
    setSponsors((prev) => prev.map((s) => (s.id === updated.id ? updated : s)));
    // If history panel is open for this sponsor, refresh it
    if (historyFor?.id === updated.id) {
      setHistoryFor(updated);
    }
    setSelectedSponsor(null);
    flash(`✅ ${updated.name} updated to ${formatINR(updated.current_commitment)}.`);
  }

  // ── totals ───────────────────────────────────────────────────────────────
  const totalOriginal = sponsors.reduce((s, x) => s + parseFloat(x.original_commitment), 0);
  const totalCurrent = sponsors.reduce((s, x) => s + parseFloat(x.current_commitment), 0);

  // ── render ───────────────────────────────────────────────────────────────
  return (
    <div style={{ maxWidth: '900px', margin: '0 auto', padding: '16px', fontFamily: 'Arial, sans-serif' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
        <h1 style={{ margin: 0, fontSize: '24px' }}>EventMind — Sponsor Dashboard</h1>
        <span style={{ fontSize: '13px', color: '#555' }}>{dbStatus}</span>
      </div>

      {/* Flash message */}
      {flashMsg && (
        <div
          style={{
            border: '1px solid #28a745',
            backgroundColor: '#d4edda',
            color: '#155724',
            borderRadius: '6px',
            padding: '10px 14px',
            marginBottom: '12px',
            fontSize: '14px',
          }}
        >
          {flashMsg}
        </div>
      )}

      {/* Add sponsor form */}
      <AddSponsorForm onAdded={handleAdded} />

      {/* Sponsors table */}
      <div style={{ border: '1px solid #ccc', borderRadius: '8px', padding: '12px', marginBottom: '12px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
          <h2 style={{ margin: 0, fontSize: '18px' }}>Sponsors &amp; Commitments</h2>
          <button
            type="button"
            onClick={loadSponsors}
            style={{ fontSize: '13px', background: 'none', border: '1px solid #aaa', borderRadius: '4px', padding: '3px 10px', cursor: 'pointer' }}
          >
            ↻ Refresh
          </button>
        </div>

        {loading && <p style={{ color: '#666' }}>Loading…</p>}
        {listError && (
          <p style={{ color: '#c00', fontSize: '14px' }}>
            Could not load sponsors: {listError}
          </p>
        )}

        {!loading && !listError && sponsors.length === 0 && (
          <p style={{ color: '#888', fontSize: '14px' }}>No sponsors yet. Add one above.</p>
        )}

        {!loading && sponsors.length > 0 && (
          <>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
              <thead>
                <tr style={{ borderBottom: '2px solid #ddd' }}>
                  <th style={{ textAlign: 'left', padding: '6px 8px' }}>Sponsor</th>
                  <th style={{ textAlign: 'left', padding: '6px 8px' }}>Original</th>
                  <th style={{ textAlign: 'left', padding: '6px 8px' }}>Current</th>
                  <th style={{ textAlign: 'left', padding: '6px 8px' }}>Last updated</th>
                  <th style={{ padding: '6px 8px' }}></th>
                </tr>
              </thead>
              <tbody>
                {sponsors.map((s) => (
                  <tr
                    key={s.id}
                    style={{
                      borderBottom: '1px solid #eee',
                      cursor: 'pointer',
                      backgroundColor:
                        historyFor?.id === s.id
                          ? '#eef4ff'
                          : parseFloat(s.original_commitment) !== parseFloat(s.current_commitment)
                          ? '#fffbea'
                          : undefined,
                    }}
                    onClick={() => handleSponsorClick(s)}
                    title="Click to toggle history"
                  >
                    <td style={{ padding: '7px 8px', fontWeight: 500 }}>{s.name}</td>
                    <td style={{ padding: '7px 8px' }}>{formatINR(s.original_commitment)}</td>
                    <td
                      style={{
                        padding: '7px 8px',
                        color:
                          parseFloat(s.original_commitment) !== parseFloat(s.current_commitment)
                            ? '#c05000'
                            : undefined,
                        fontWeight:
                          parseFloat(s.original_commitment) !== parseFloat(s.current_commitment) ? 600 : undefined,
                      }}
                    >
                      {formatINR(s.current_commitment)}
                    </td>
                    <td style={{ padding: '7px 8px', fontSize: '13px', color: '#555' }}>
                      {formatDate(s.updated_at)}
                    </td>
                    <td style={{ padding: '7px 8px', textAlign: 'right' }}>
                      <button
                        type="button"
                        onClick={(e) => handleEditClick(s, e)}
                        style={{
                          fontSize: '12px',
                          background: '#f0f0f0',
                          border: '1px solid #ccc',
                          borderRadius: '4px',
                          padding: '3px 8px',
                          cursor: 'pointer',
                        }}
                      >
                        Edit
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
              <tfoot>
                <tr style={{ borderTop: '2px solid #ddd', fontWeight: 600 }}>
                  <td style={{ padding: '7px 8px' }}>Total</td>
                  <td style={{ padding: '7px 8px' }}>{formatINR(totalOriginal)}</td>
                  <td style={{ padding: '7px 8px', color: totalCurrent < totalOriginal ? '#c05000' : '#155724' }}>
                    {formatINR(totalCurrent)}
                  </td>
                  <td colSpan={2}></td>
                </tr>
              </tfoot>
            </table>
            <p style={{ fontSize: '12px', color: '#888', margin: '6px 0 0' }}>
              Click a row to view change history. Rows in yellow have changed commitments.
            </p>
          </>
        )}
      </div>

      {/* History panel */}
      {historyFor && (
        <HistoryPanel sponsor={historyFor} onClose={() => setHistoryFor(null)} />
      )}

      {/* Update form */}
      {selectedSponsor && (
        <UpdateForm
          sponsor={selectedSponsor}
          onUpdated={handleUpdated}
          onCancel={() => setSelectedSponsor(null)}
        />
      )}
    </div>
  );
}

export default App;
