import { useState } from 'react';
import * as api from '../api/semanticAPI';
import { Flame, Upload, FileJson, AlertCircle, Check, Loader2 } from 'lucide-react';

export function CacheWarmup() {
  const [file, setFile] = useState<File | null>(null);
  const [pasteText, setPasteText] = useState('');
  const [mode, setMode] = useState<'file' | 'paste'>('paste');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<api.WarmupResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const parseEntries = (): api.WarmupEntry[] => {
    if (mode === 'paste') {
      try {
        const parsed = JSON.parse(pasteText);
        const arr = Array.isArray(parsed) ? parsed : parsed.entries || [];
        return arr.map((e: any) => ({
          prompt: String(e.prompt ?? e.query ?? ''),
          response: String(e.response ?? e.answer ?? e.content ?? ''),
          model: e.model,
        })).filter((e: api.WarmupEntry) => e.prompt && e.response);
      } catch {
        return [];
      }
    }
    return [];
  };

  const parseFile = async (f: File): Promise<api.WarmupEntry[]> => {
    const text = await f.text();
    const lines = text.trim().split(/\r?\n/);
    const entries: api.WarmupEntry[] = [];
    const isJsonl = lines[0]?.trim().startsWith('{');
    if (isJsonl) {
      for (const line of lines) {
        try {
          const o = JSON.parse(line);
          entries.push({
            prompt: String(o.prompt ?? o.query ?? ''),
            response: String(o.response ?? o.answer ?? o.content ?? ''),
            model: o.model,
          });
        } catch {}
      }
    } else {
      const parseCSVLine = (line: string): string[] => {
        const out: string[] = [];
        let cur = '';
        let inQ = false;
        for (let i = 0; i < line.length; i++) {
          const c = line[i];
          if (c === '"') inQ = !inQ;
          else if (c === ',' && !inQ) {
            out.push(cur.replace(/^"|"$/g, '').trim());
            cur = '';
          } else cur += c;
        }
        out.push(cur.replace(/^"|"$/g, '').trim());
        return out;
      };
      const header = parseCSVLine(lines[0] || '').map((s) => s.toLowerCase());
      const promptIdx = header.findIndex((h) => h === 'prompt' || h === 'query');
      const responseIdx = header.findIndex((h) => h === 'response' || h === 'answer' || h === 'content');
      const modelIdx = header.findIndex((h) => h === 'model');
      if (promptIdx < 0 || responseIdx < 0) return [];
      for (let i = 1; i < lines.length; i++) {
        const cells = parseCSVLine(lines[i]);
        const prompt = cells[promptIdx] || '';
        const response = cells[responseIdx] || '';
        if (prompt && response) {
          entries.push({
            prompt,
            response,
            model: modelIdx >= 0 ? cells[modelIdx] : undefined,
          });
        }
      }
    }
    return entries.filter((e) => e.prompt && e.response);
  };

  const handleWarmup = async () => {
    setError(null);
    setResult(null);
    setLoading(true);
    try {
      let entries: api.WarmupEntry[];
      if (mode === 'file' && file) {
        entries = await parseFile(file);
      } else {
        entries = parseEntries();
      }
      if (entries.length === 0) {
        setError('No valid entries found. Each entry needs prompt and response.');
        return;
      }
      if (entries.length > 500) {
        setError('Maximum 500 entries per request. Split your file.');
        return;
      }
      const res = await api.warmupCache(entries, true);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Warmup failed');
    } finally {
      setLoading(false);
    }
  };

  const exampleJson = `[
  {"prompt": "What is your refund policy?", "response": "We offer 30-day refunds..."},
  {"prompt": "How do I cancel?", "response": "You can cancel from Settings..."}
]`;

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <Flame size={22} style={{ color: '#f59e0b' }} />
        <h3 style={styles.title}>Cache Warm-Up</h3>
      </div>
      <p style={styles.description}>
        Pre-populate your cache with historical queries so you get semantic hits from day one.
        Upload a CSV or JSON file, or paste JSON.
      </p>

      <div style={styles.tabs}>
        <button
          style={{ ...styles.tab, ...(mode === 'paste' ? styles.tabActive : {}) }}
          onClick={() => setMode('paste')}
        >
          <FileJson size={16} /> Paste JSON
        </button>
        <button
          style={{ ...styles.tab, ...(mode === 'file' ? styles.tabActive : {}) }}
          onClick={() => setMode('file')}
        >
          <Upload size={16} /> Upload File
        </button>
      </div>

      {mode === 'paste' ? (
        <textarea
          value={pasteText}
          onChange={(e) => setPasteText(e.target.value)}
          placeholder={exampleJson}
          style={styles.textarea}
          rows={8}
        />
      ) : (
        <div style={styles.fileZone}>
          <input
            type="file"
            accept=".json,.jsonl,.csv"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            style={styles.fileInput}
          />
          <p style={styles.fileHint}>
            {file ? file.name : 'Choose CSV or JSON/JSONL file'}
          </p>
          <p style={styles.fileFormat}>
            CSV: prompt,response,model (optional) | JSON: array of objects with prompt and response
          </p>
        </div>
      )}

      <button
        onClick={handleWarmup}
        disabled={loading || (mode === 'paste' && !pasteText.trim()) || (mode === 'file' && !file)}
        style={styles.button}
      >
        {loading ? (
          <><Loader2 size={18} style={{ animation: 'spin 1s linear infinite' }} /> Warming cache...</>
        ) : (
          <><Flame size={18} /> Warm Cache</>
        )}
      </button>

      {result && (
        <div style={styles.result}>
          <Check size={18} style={{ color: '#10b981' }} />
          <span>Added {result.added}, skipped {result.skipped}, errors {result.errors}</span>
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
    background: 'rgba(245, 158, 11, 0.08)',
    border: '1px solid rgba(245, 158, 11, 0.25)',
    borderRadius: '12px',
    padding: '24px',
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
  description: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.7)',
    marginBottom: '20px',
    lineHeight: '1.5',
  },
  tabs: {
    display: 'flex',
    gap: '8px',
    marginBottom: '16px',
  },
  tab: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    padding: '8px 16px',
    background: 'rgba(255, 255, 255, 0.05)',
    border: '1px solid rgba(255, 255, 255, 0.15)',
    borderRadius: '8px',
    color: 'rgba(255, 255, 255, 0.8)',
    fontSize: '14px',
    cursor: 'pointer',
  },
  tabActive: {
    background: 'rgba(245, 158, 11, 0.2)',
    borderColor: 'rgba(245, 158, 11, 0.4)',
    color: '#fbbf24',
  },
  textarea: {
    width: '100%',
    padding: '12px',
    fontSize: '13px',
    fontFamily: 'monospace',
    background: 'rgba(0, 0, 0, 0.3)',
    border: '1px solid rgba(255, 255, 255, 0.2)',
    borderRadius: '8px',
    color: '#e5e7eb',
    marginBottom: '16px',
    resize: 'vertical',
  },
  fileZone: {
    padding: '20px',
    background: 'rgba(0, 0, 0, 0.2)',
    border: '1px dashed rgba(255, 255, 255, 0.3)',
    borderRadius: '8px',
    marginBottom: '16px',
    textAlign: 'center',
  },
  fileInput: {
    display: 'block',
    margin: '0 auto 8px',
  },
  fileHint: {
    fontSize: '14px',
    color: 'rgba(255, 255, 255, 0.6)',
    margin: '0 0 4px 0',
  },
  fileFormat: {
    fontSize: '12px',
    color: 'rgba(255, 255, 255, 0.4)',
    margin: 0,
  },
  button: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '8px',
    width: '100%',
    padding: '12px 24px',
    fontSize: '15px',
    fontWeight: '600',
    background: 'linear-gradient(135deg, #f59e0b, #d97706)',
    border: 'none',
    borderRadius: '8px',
    color: '#fff',
    cursor: 'pointer',
  },
  result: {
    display: 'flex',
    alignItems: 'center',
    gap: '8px',
    marginTop: '16px',
    padding: '12px',
    background: 'rgba(16, 185, 129, 0.15)',
    border: '1px solid rgba(16, 185, 129, 0.3)',
    borderRadius: '8px',
    color: '#6ee7b7',
    fontSize: '14px',
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
