import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';
import { vscDarkPlus } from 'react-syntax-highlighter/dist/esm/styles/prism';
import { Copy, Check } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

/**
 * MarkdownRenderer Component
 *
 * A beautiful, Streamlit-inspired markdown renderer for chat messages.
 * Supports all standard markdown features with professional styling.
 *
 * Features:
 * - Headings (H1-H6) with proper hierarchy
 * - Lists (ordered, unordered, nested)
 * - Tables with clean styling
 * - Code blocks with syntax highlighting
 * - Inline code with distinct background
 * - Blockquotes with elegant styling
 * - Bold, italic, strikethrough text
 * - Links with hover effects
 * - Horizontal rules
 * - Images
 * - Emojis
 * - Dark/light mode support
 */
export const MarkdownRenderer = React.memo(({ content, className }: MarkdownRendererProps) => {
  const [copiedCode, setCopiedCode] = useState<string | null>(null);

  const handleCopyCode = async (code: string, id: string) => {
    await navigator.clipboard.writeText(code);
    setCopiedCode(id);
    setTimeout(() => setCopiedCode(null), 2000);
  };

  return (
    <div className={cn('markdown-content', className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          // Headings with Streamlit-inspired styling
          h1: ({ children }) => (
            <h1 className="text-3xl font-bold mt-6 mb-4 pb-2 border-b-2 border-border text-foreground">
              {children}
            </h1>
          ),
          h2: ({ children }) => (
            <h2 className="text-2xl font-bold mt-5 mb-3 pb-2 border-b border-border text-foreground">
              {children}
            </h2>
          ),
          h3: ({ children }) => (
            <h3 className="text-xl font-semibold mt-4 mb-2 text-foreground">
              {children}
            </h3>
          ),
          h4: ({ children }) => (
            <h4 className="text-lg font-semibold mt-3 mb-2 text-foreground">
              {children}
            </h4>
          ),
          h5: ({ children }) => (
            <h5 className="text-base font-semibold mt-3 mb-2 text-foreground">
              {children}
            </h5>
          ),
          h6: ({ children }) => (
            <h6 className="text-sm font-semibold mt-3 mb-2 text-muted-foreground uppercase tracking-wide">
              {children}
            </h6>
          ),

          // Paragraphs with proper spacing
          p: ({ children }) => (
            <p className="text-base leading-relaxed my-3 text-foreground">
              {children}
            </p>
          ),

          // Strong (bold) text
          strong: ({ children }) => (
            <strong className="font-semibold text-foreground">
              {children}
            </strong>
          ),

          // Emphasis (italic) text
          em: ({ children }) => (
            <em className="italic text-foreground">
              {children}
            </em>
          ),

          // Strikethrough text
          del: ({ children }) => (
            <del className="line-through text-muted-foreground">
              {children}
            </del>
          ),

          // Links with hover effects
          a: ({ href, children }) => (
            <a
              href={href}
              target="_blank"
              rel="noopener noreferrer"
              className="text-blue-600 dark:text-blue-400 hover:text-blue-800 dark:hover:text-blue-300 underline decoration-2 underline-offset-2 transition-colors"
            >
              {children}
            </a>
          ),

          // Blockquotes with elegant styling
          blockquote: ({ children }) => (
            <blockquote className="border-l-4 border-blue-500 dark:border-blue-400 bg-blue-50 dark:bg-blue-950/30 pl-4 pr-4 py-2 my-4 italic text-foreground">
              {children}
            </blockquote>
          ),

          // Code blocks with syntax highlighting
          code: ({ inline, className, children, ...props }: any) => {
            const match = /language-(\w+)/.exec(className || '');
            const codeString = String(children).replace(/\n$/, '');
            const codeId = `code-${Math.random().toString(36).substr(2, 9)}`;

            if (!inline && match) {
              return (
                <div className="relative group/code my-4">
                  <div className="flex items-center justify-between bg-gray-800 dark:bg-gray-900 px-4 py-2 rounded-t-md border-b border-gray-700">
                    <span className="text-xs text-gray-300 font-mono">
                      {match[1]}
                    </span>
                    <button
                      onClick={() => handleCopyCode(codeString, codeId)}
                      className="flex items-center gap-1 px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded text-xs text-gray-200 transition-colors"
                      aria-label="Copy code"
                    >
                      {copiedCode === codeId ? (
                        <>
                          <Check className="h-3 w-3" />
                          <span>Copied!</span>
                        </>
                      ) : (
                        <>
                          <Copy className="h-3 w-3" />
                          <span>Copy</span>
                        </>
                      )}
                    </button>
                  </div>
                  <SyntaxHighlighter
                    style={vscDarkPlus}
                    language={match[1]}
                    PreTag="div"
                    customStyle={{
                      margin: 0,
                      borderTopLeftRadius: 0,
                      borderTopRightRadius: 0,
                      borderBottomLeftRadius: '0.375rem',
                      borderBottomRightRadius: '0.375rem',
                      fontSize: '0.875rem',
                      lineHeight: '1.5',
                    }}
                    {...props}
                  >
                    {codeString}
                  </SyntaxHighlighter>
                </div>
              );
            }

            // Inline code
            return (
              <code
                className="bg-gray-100 dark:bg-gray-800 text-pink-600 dark:text-pink-400 px-1.5 py-0.5 rounded text-[0.875em] font-mono border border-gray-200 dark:border-gray-700"
                {...props}
              >
                {children}
              </code>
            );
          },

          // Unordered lists
          ul: ({ children }) => (
            <ul className="list-disc list-outside ml-6 my-3 space-y-1 text-foreground">
              {children}
            </ul>
          ),

          // Ordered lists
          ol: ({ children }) => (
            <ol className="list-decimal list-outside ml-6 my-3 space-y-1 text-foreground">
              {children}
            </ol>
          ),

          // List items
          li: ({ children }) => (
            <li className="text-base leading-relaxed pl-2">
              {children}
            </li>
          ),

          // Tables with clean, professional styling
          table: ({ children }) => (
            <div className="overflow-x-auto my-4">
              <table className="min-w-full divide-y divide-gray-300 dark:divide-gray-700 border border-gray-300 dark:border-gray-700 rounded-lg">
                {children}
              </table>
            </div>
          ),

          // Table head
          thead: ({ children }) => (
            <thead className="bg-gray-50 dark:bg-gray-800">
              {children}
            </thead>
          ),

          // Table body
          tbody: ({ children }) => (
            <tbody className="divide-y divide-gray-200 dark:divide-gray-700 bg-white dark:bg-gray-900">
              {children}
            </tbody>
          ),

          // Table row
          tr: ({ children }) => (
            <tr className="hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors">
              {children}
            </tr>
          ),

          // Table header cell
          th: ({ children }) => (
            <th className="px-4 py-3 text-left text-xs font-semibold text-gray-700 dark:text-gray-300 uppercase tracking-wider">
              {children}
            </th>
          ),

          // Table data cell
          td: ({ children }) => (
            <td className="px-4 py-3 text-sm text-foreground whitespace-nowrap">
              {children}
            </td>
          ),

          // Horizontal rule
          hr: () => (
            <hr className="my-6 border-t-2 border-gray-200 dark:border-gray-700" />
          ),

          // Images
          img: ({ src, alt }) => (
            <img
              src={src}
              alt={alt}
              className="max-w-full h-auto rounded-lg shadow-md my-4"
              loading="lazy"
            />
          ),

          // Task lists (GitHub Flavored Markdown)
          input: ({ type, checked, disabled }) => {
            if (type === 'checkbox') {
              return (
                <input
                  type="checkbox"
                  checked={checked}
                  disabled={disabled}
                  className="mr-2 rounded border-gray-300 dark:border-gray-600"
                  readOnly
                />
              );
            }
            return null;
          },
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
});

MarkdownRenderer.displayName = 'MarkdownRenderer';
