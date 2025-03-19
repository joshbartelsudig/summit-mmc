'use client'

import React from 'react';
import ReactMarkdown from 'react-markdown';
import rehypeRaw from 'rehype-raw';
import remarkGfm from 'remark-gfm';
import { CodeBlock } from './code-block';
import { cn } from '@/lib/utils';

interface MarkdownRendererProps {
  content: string;
  className?: string;
}

// Function to process text and highlight function names
const processFunctionNames = (text: string) => {
  // Create a React fragment to hold all elements
  const elements: React.ReactNode[] = [];
  let lastIndex = 0;

  // Find all function names that are not part of code blocks
  const regex = /(?<!`)\b(\w+)\(\)(?!`)/g;
  let match;

  while ((match = regex.exec(text)) !== null) {
    // Add text before the match
    if (match.index > lastIndex) {
      elements.push(text.slice(lastIndex, match.index));
    }

    // Add the function name with styling
    elements.push(
      <code
        key={match.index}
        className="font-mono text-blue-500 dark:text-blue-400 bg-transparent px-0"
      >
        {match[0]}
      </code>
    );

    lastIndex = match.index + match[0].length;
  }

  // Add any remaining text
  if (lastIndex < text.length) {
    elements.push(text.slice(lastIndex));
  }

  return elements;
};

export function MarkdownRenderer({ content, className }: MarkdownRendererProps) {
  return (
    <div className={cn('markdown-content prose prose-sm dark:prose-invert max-w-none', className)}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeRaw]}
        components={{
          // Handle code blocks and inline code
          code({ className, children, ...props }) {
            // For inline code, return a simple styled code element
            if (className?.includes('inline')) {
              return (
                <code className="rounded-sm px-1 py-0.5 font-mono text-sm bg-muted" {...props}>
                  {children}
                </code>
              );
            }

            // For code blocks, detect language and use CodeBlock component
            const match = /language-(\w+)/.exec(className || '');
            const language = match ? match[1] : '';
            const value = String(children).replace(/\n$/, '');

            return (
              <CodeBlock
                language={language}
                value={value}
                {...props}
              />
            );
          },
          // Process paragraphs and highlight function names
          p({ children }) {
            if (typeof children === 'string') {
              return (
                <div className="whitespace-pre-wrap mb-4">
                  {processFunctionNames(children)}
                </div>
              );
            }
            // If children is not a string (e.g., contains other elements), render normally
            return <div className="whitespace-pre-wrap mb-4">{children}</div>;
          },
          // Better table styling
          table({ children }) {
            return (
              <div className="my-4 overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200 dark:divide-gray-700">
                  {children}
                </table>
              </div>
            );
          },
          // Style table headers
          th({ children }) {
            return (
              <th className="px-4 py-2 text-left text-sm font-semibold bg-gray-50 dark:bg-gray-800">
                {children}
              </th>
            );
          },
          // Style table cells
          td({ children }) {
            return (
              <td className="px-4 py-2 text-sm border-t border-gray-100 dark:border-gray-800">
                {children}
              </td>
            );
          }
        }}
      >
        {content}
      </ReactMarkdown>
    </div>
  );
}
