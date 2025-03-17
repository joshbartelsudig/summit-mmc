'use client'

import React, { useEffect, useState } from 'react';
import { Check, Copy } from 'lucide-react';
import { cn } from '@/lib/utils';
import mermaid from 'mermaid';
import hljs from 'highlight.js';
import 'highlight.js/styles/tokyo-night-dark.css';

// Initialize mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'neutral',
  securityLevel: 'loose',
  gantt: {
    titleTopMargin: 25,
    barHeight: 20,
    barGap: 4,
    topPadding: 50,
    leftPadding: 75,
    gridLineStartPadding: 35,
    fontSize: 11,
    numberSectionStyles: 4,
    axisFormat: '%Y-%m-%d',
  }
});

interface CodeBlockProps {
  language: string;
  value: string;
  className?: string;
}

export function CodeBlock({ language, value, className }: CodeBlockProps) {
  const [copied, setCopied] = useState(false);
  const [renderedContent, setRenderedContent] = useState<string>(value);
  const [isLoading, setIsLoading] = useState(language === 'mermaid');
  const [error, setError] = useState<string | null>(null);

  // Handle Mermaid diagrams and code highlighting
  useEffect(() => {
    const renderContent = async () => {
      try {
        if (language === 'mermaid') {
          setIsLoading(true);
          const id = `mermaid-${Math.random().toString(36).substring(2)}`;
          const { svg } = await mermaid.render(id, value);
          setRenderedContent(svg);
          setError(null);
        } else if (language) {
          // Highlight code if language is specified
          const highlighted = hljs.highlight(value, { language }).value;
          setRenderedContent(highlighted);
          setError(null);
        } else {
          // Plain text, just escape HTML
          setRenderedContent(
            value
              .replace(/&/g, '&amp;')
              .replace(/</g, '&lt;')
              .replace(/>/g, '&gt;')
              .replace(/"/g, '&quot;')
              .replace(/'/g, '&#039;')
          );
        }
      } catch (err) {
        console.error('Error rendering content:', err);
        setError(language === 'mermaid' ? 'Failed to render diagram' : 'Failed to highlight code');
        setRenderedContent(value); // Fallback to plain text
      } finally {
        setIsLoading(false);
      }
    };

    renderContent();
  }, [language, value]);

  const handleCopy = () => {
    navigator.clipboard.writeText(value);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={cn(
      'relative rounded-md overflow-hidden',
      'bg-[#1a1b26] dark:bg-[#1a1b26]', // Tokyo Night Dark theme
      className
    )}>
      {/* Copy button */}
      <div className="absolute right-2 top-2 z-10">
        <button
          onClick={handleCopy}
          className="rounded bg-white/10 p-2 hover:bg-white/20 text-gray-400 hover:text-white transition-colors"
        >
          {copied ? <Check className="h-4 w-4" /> : <Copy className="h-4 w-4" />}
          <span className="sr-only">Copy code</span>
        </button>
      </div>

      {/* Language indicator */}
      {language && (
        <div className="absolute left-2 top-2 text-xs text-gray-400 font-mono bg-white/5 px-2 py-1 rounded">
          {language}
        </div>
      )}

      {/* Content */}
      <div className="mt-8 p-4">
        {isLoading ? (
          <div className="text-gray-400">Loading...</div>
        ) : error ? (
          <div className="text-red-400">
            {error}
            <pre className="mt-2 overflow-x-auto text-gray-300">
              <code>{value}</code>
            </pre>
          </div>
        ) : language === 'mermaid' ? (
          <div 
            className="bg-white dark:bg-transparent rounded-md overflow-auto"
            dangerouslySetInnerHTML={{ __html: renderedContent }}
          />
        ) : (
          <pre className="!m-0 !p-0 !bg-transparent overflow-x-auto font-mono text-[15px] leading-relaxed">
            <code
              className={cn(
                'language-' + language,
                'text-gray-300 !bg-transparent',
                'block w-fit min-w-full'
              )}
              dangerouslySetInnerHTML={{ __html: renderedContent }}
            />
          </pre>
        )}
      </div>
    </div>
  );
}
