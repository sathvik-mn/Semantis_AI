import { useState, useEffect, useCallback } from 'react';
import * as api from '../api/semanticAPI';
import { Database, Search, Trash2, ChevronLeft, ChevronRight, Loader2, AlertCircle } from 'lucide-react';

export function CacheManager() {
  const [entries, setEntries] = useState<api.CacheEntryItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState<Set<number>>(new Set());
  const [deleting, setDeleting] = useState(false);
  const PAGE_SIZE = 20;

  const fetchEntries = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await api.listCacheEntries(PAGE_SIZE, page * PAGE_SIZE, search || undefined);
      setEntries(res.entries);
      setTotal(res.total);
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Failed to load entries';
      setError(message);
    } finally {
      setLoading(false);
    }
  }, [page, search]);

  useEffect(() => { fetchEntries(); }, [fetchEntries]);

  const handleSearch = () => {
    setPage(0);
    setSearch(searchInput);
  };

  const toggleSelect = (id: number) => {
    setSelected(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  const toggleSelectAll = () => {
    if (selected.size === entries.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(entries.map(e => e.id)));
    }
  };

  const handleDelete = async () => {
    if (selected.size === 0) return;
    setDeleting(true);
    setError(null);
    try {
      await api.deleteCacheEntries(Array.from(selected));
      setSelected(new Set());
      await fetchEntries();
    } catch (err: unknown) {
      const message = err instanceof Error ? err.message : 'Delete failed';
      setError(message);
    } finally {
      setDeleting(false);
    }
  };

  const totalPages = Math.ceil(total / PAGE_SIZE);

  const formatDate = (d: string | null) => {
    if (!d) return '—';
    try { return new Date(d).toLocaleDateString(); } catch { return d; }
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <Database size={22} style={{ color: '#6366f1' }} />
        <h3 style={styles.title}>Cache Entries</h3>
        <span style={styles.badge}>{total}</span>
      </div>
      <p style={styles.description}>
        View, search, and manage your cached prompt-response pairs.
      </p>

      {/* Search bar */}
      <div style={styles.searchRow}>
        <div style={styles.searchInputWrap}>
          <Search size={16} style={{ color: 'rgba(255,255,255,0.4)', flexShrink: 0 }} />
          <input
            type="text"
            value={searchInput}
            onChange={e => setSearchInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleSearch()}
            placeholder="Search prompts..."
            style={styles.searchInput}
          />
        </div>
        <button type="button" onClick={handleSearch} style={styles.searchBtn}>Search</button>
        {selected.size > 0 && (
          <button
            type="button"
            onClick={handleDelete}
            disabled={deleting}
            style={styles.deleteBtn}
          >
            {deleting ? <Loader2 size={14} style={{ animation: 'spin 1s linear infinite' }} /> : <Trash2 size={14} />}
            Delete {selected.size}
          </button>
        )}
      </div>

      {/* Table */}
      {loading ? (
        <div style={styles.loadingWrap}>
          <Loader2 size={24} style={{ animation: 'spin 1s linear infinite', color: '#6366f1' }} />
        </div>
      ) : entries.length === 0 ? (
        <div style={styles.empty}>
          {search ? 'No entries match your search.' : 'No cache entries yet. Use Cache Warm-Up to add entries.'}
        </div>
      ) : (
        <div style={styles.tableWrap}>
          <table style={styles.table}>
            <thead>
              <tr>
                <th style={styles.th}>
                  <input
                    type="checkbox"
                    checked={selected.size === entries.length && entries.length > 0}
                    onChange={toggleSelectAll}
                    title="Select all"
                  />
                </th>
                <th style={styles.th}>Prompt</th>
                <th style={styles.th}>Response</th>
                <th style={styles.th}>Model</th>
                <th style={styles.th}>Uses</th>
                <th style={styles.th}>Created</th>
              </tr>
            </thead>
            <tbody>
              {entries.map(entry => (
                <tr
                  key={entry.id}
                  style={{
                    ...styles.tr,
                    background: selected.has(entry.id) ? 'rgba(99,102,241,0.15)' : undefined,
                  }}
                >
                  <td style={styles.td}>
                    <input
                      type="checkbox"
                      checked={selected.has(entry.id)}
                      onChange={() => toggleSelect(entry.id)}
                    />
                  </td>
                  <td style={{ ...styles.td, ...styles.promptCell }} title={entry.prompt_norm}>
                    {entry.prompt_norm.length > 80 ? entry.prompt_norm.slice(0, 80) + '...' : entry.prompt_norm}
                  </td>
                  <td style={{ ...styles.td, ...styles.responseCell }} title={entry.response_text}>
                    {entry.response_text.length > 60 ? entry.response_text.slice(0, 60) + '...' : entry.response_text}
                  </td>
                  <td style={styles.td}>{entry.model}</td>
                  <td style={styles.td}>{entry.use_count}</td>
                  <td style={styles.td}>{formatDate(entry.created_at)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <div style={styles.pagination}>
          <button
            type="button"
            onClick={() => setPage(p => Math.max(0, p - 1))}
            disabled={page === 0}
            style={styles.pageBtn}
          >
            <ChevronLeft size={16} />
          </button>
          <span style={styles.pageInfo}>
            Page {page + 1} of {totalPages}
          </span>
          <button
            type="button"
            onClick={() => setPage(p => Math.min(totalPages - 1, p + 1))}
            disabled={page >= totalPages - 1}
            style={styles.pageBtn}
          >
            <ChevronRight size={16} />
          </button>
        </div>
      )}

      {error && (
        <div style={styles.error}>
          <AlertCircle size={16} />
          {error}
        </div>
      )}

      <style>{`@keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }`}</style>
    </div>
  );
}

const styles: Record<string, React.CSSProperties> = {
  container: {
    background: 'rgba(99, 102, 241, 0.08)',
    border: '1px solid rgba(99, 102, 241, 0.25)',
    borderRadius: '12px',
    padding: '24px',
    marginTop: '24px',
  },
  header: {
    display: 'flex',
    alignItems: 'center',
    gap: '12px',
    marginBottom: '8px',
  },
  title: {
    fontSize: '20px',
    color: '#fff',
    margin: 0,
    fontWeight: '600',
  },
  badge: {
    background: 'rgba(99, 102, 241, 0.3)',
    color: '#a5b4fc',
    padding: '2px 10px',
    borderRadius: '12px',
    fontSize: '13px',
    fontWeight: '600',
  },
  description: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: '16px',
    lineHeight: '1.5',
  },
  searchRow: {
    display: 'flex',
    gap: '8px',
    marginBottom: '16px',
    alignItems: 'center',
  },
  searchInputWrap: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    flex: 1,
    padding: '8px 12px',
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    borderRadius: '8px',
  },
  searchInput: {
    flex: 1,
    background: 'transparent',
    border: 'none',
    color: '#e5e7eb',
    fontSize: '14px',
    outline: 'none',
  },
  searchBtn: {
    padding: '8px 16px',
    background: 'rgba(99, 102, 241, 0.2)',
    border: '1px solid rgba(99, 102, 241, 0.4)',
    borderRadius: '8px',
    color: '#a5b4fc',
    fontSize: '14px',
    cursor: 'pointer',
  },
  deleteBtn: {
    display: 'flex',
    alignItems: 'center',
    gap: '6px',
    padding: '8px 16px',
    background: 'rgba(239, 68, 68, 0.2)',
    border: '1px solid rgba(239, 68, 68, 0.4)',
    borderRadius: '8px',
    color: '#fca5a5',
    fontSize: '14px',
    cursor: 'pointer',
  },
  tableWrap: {
    overflowX: 'auto',
    borderRadius: '8px',
    border: '1px solid rgba(255, 255, 255, 0.1)',
  },
  table: {
    width: '100%',
    borderCollapse: 'collapse',
    fontSize: '13px',
  },
  th: {
    textAlign: 'left',
    padding: '10px 12px',
    color: 'rgba(255, 255, 255, 0.5)',
    fontWeight: '500',
    fontSize: '12px',
    textTransform: 'uppercase',
    letterSpacing: '0.05em',
    borderBottom: '1px solid rgba(255, 255, 255, 0.1)',
    whiteSpace: 'nowrap',
  },
  tr: {
    borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
  },
  td: {
    padding: '10px 12px',
    color: 'rgba(255, 255, 255, 0.8)',
    whiteSpace: 'nowrap',
  },
  promptCell: {
    maxWidth: '250px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  responseCell: {
    maxWidth: '200px',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  loadingWrap: {
    display: 'flex',
    justifyContent: 'center',
    padding: '32px',
  },
  empty: {
    textAlign: 'center',
    padding: '32px',
    color: 'rgba(255, 255, 255, 0.4)',
    fontSize: '14px',
  },
  pagination: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '12px',
    marginTop: '16px',
  },
  pageBtn: {
    display: 'flex',
    alignItems: 'center',
    padding: '6px 10px',
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    borderRadius: '6px',
    color: 'rgba(255, 255, 255, 0.7)',
    cursor: 'pointer',
  },
  pageInfo: {
    fontSize: '13px',
    color: 'rgba(255, 255, 255, 0.5)',
  },
  error: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginTop: '16px',
    padding: '12px',
    background: 'rgba(239, 68, 68, 0.15)',
    border: '1px solid rgba(239, 68, 68, 0.3)',
    borderRadius: '8px',
    color: '#fca5a5',
    fontSize: '14px',
  },
};
