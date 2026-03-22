import { memo, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check } from 'lucide-react';

function CodeBlock({ language, children }: { language: string; children: string }) {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    navigator.clipboard.writeText(children);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div style={{ position: 'relative', margin: '12px 0' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        padding: '6px 12px',
        background: '#1a1b26',
        borderRadius: '8px 8px 0 0',
        borderBottom: '1px solid rgba(255,255,255,0.08)',
      }}>
        <span style={{ fontSize: '12px', color: 'rgba(255,255,255,0.4)', fontFamily: 'monospace' }}>
          {language || 'code'}
        </span>
        <button
          onClick={handleCopy}
          title="Copy code"
          style={{
            display: 'flex', alignItems: 'center', gap: '4px',
            background: 'none', border: 'none', color: 'rgba(255,255,255,0.4)',
            cursor: 'pointer', fontSize: '12px', padding: '2px 6px',
            borderRadius: '4px', transition: 'color 0.15s',
          }}
        >
          {copied ? <Check size={12} /> : <Copy size={12} />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <SyntaxHighlighter
        style={oneDark}
        language={language || 'text'}
        PreTag="div"
        customStyle={{
          margin: 0,
          borderRadius: '0 0 8px 8px',
          fontSize: '13px',
          lineHeight: '1.5',
          padding: '14px',
        }}
      >
        {children}
      </SyntaxHighlighter>
    </div>
  );
}

interface MarkdownRendererProps {
  content: string;
}

export const MarkdownRenderer = memo(function MarkdownRenderer({ content }: MarkdownRendererProps) {
  return (
    <div style={{ color: 'rgba(255,255,255,0.88)', fontSize: '14px', lineHeight: '1.7', wordBreak: 'break-word' }}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        children={content}
        components={{
          pre({ children }) {
            return <>{children}</>;
          },
          code({ className, children, ...props }) {
            const match = /language-(\w+)/.exec(className || '');
            const codeStr = String(children).replace(/\n$/, '');

            if (match || (className && className.includes('language-'))) {
              return <CodeBlock language={match?.[1] || ''} children={codeStr} />;
            }

            const isBlock = codeStr.includes('\n');
            if (isBlock) {
              return <CodeBlock language="" children={codeStr} />;
            }

            return (
              <code
                style={{
                  background: 'rgba(255,255,255,0.08)',
                  padding: '2px 6px',
                  borderRadius: '4px',
                  fontSize: '0.9em',
                  fontFamily: "'JetBrains Mono', 'Fira Code', monospace",
                  color: '#e2b3ff',
                }}
                {...props}
              >
                {children}
              </code>
            );
          },
          p({ children }) {
            return <p style={{ margin: '0 0 12px 0', lineHeight: '1.7', color: 'inherit' }}>{children}</p>;
          },
          h1({ children }) {
            return <h1 style={{ fontSize: '1.5em', fontWeight: 700, margin: '20px 0 10px', color: '#fff' }}>{children}</h1>;
          },
          h2({ children }) {
            return <h2 style={{ fontSize: '1.3em', fontWeight: 600, margin: '18px 0 8px', color: '#fff' }}>{children}</h2>;
          },
          h3({ children }) {
            return <h3 style={{ fontSize: '1.15em', fontWeight: 600, margin: '16px 0 6px', color: '#fff' }}>{children}</h3>;
          },
          ul({ children }) {
            return <ul style={{ margin: '8px 0', paddingLeft: '20px', color: 'inherit' }}>{children}</ul>;
          },
          ol({ children }) {
            return <ol style={{ margin: '8px 0', paddingLeft: '20px', color: 'inherit' }}>{children}</ol>;
          },
          li({ children }) {
            return <li style={{ margin: '4px 0', lineHeight: '1.6', color: 'inherit' }}>{children}</li>;
          },
          blockquote({ children }) {
            return (
              <blockquote style={{
                margin: '12px 0',
                padding: '8px 16px',
                borderLeft: '3px solid #3b82f6',
                background: 'rgba(59,130,246,0.08)',
                borderRadius: '0 6px 6px 0',
                color: 'rgba(255,255,255,0.8)',
              }}>
                {children}
              </blockquote>
            );
          },
          table({ children }) {
            return (
              <div style={{ overflowX: 'auto', margin: '12px 0' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '14px' }}>
                  {children}
                </table>
              </div>
            );
          },
          th({ children }) {
            return (
              <th style={{
                padding: '8px 12px', textAlign: 'left',
                borderBottom: '2px solid rgba(255,255,255,0.15)',
                color: '#fff', fontWeight: 600, fontSize: '13px',
              }}>
                {children}
              </th>
            );
          },
          td({ children }) {
            return (
              <td style={{
                padding: '8px 12px',
                borderBottom: '1px solid rgba(255,255,255,0.06)',
                color: 'rgba(255,255,255,0.85)',
              }}>
                {children}
              </td>
            );
          },
          a({ href, children }) {
            return (
              <a href={href} target="_blank" rel="noopener noreferrer" style={{ color: '#60a5fa', textDecoration: 'none' }}>
                {children}
              </a>
            );
          },
          strong({ children }) {
            return <strong style={{ color: '#fff', fontWeight: 600 }}>{children}</strong>;
          },
          em({ children }) {
            return <em style={{ color: 'rgba(255,255,255,0.85)' }}>{children}</em>;
          },
          hr() {
            return <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.1)', margin: '16px 0' }} />;
          },
        }}
      />
    </div>
  );
});
