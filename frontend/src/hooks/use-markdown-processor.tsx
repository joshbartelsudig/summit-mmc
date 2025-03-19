'use client'

import React, { useEffect, useMemo, useState } from "react";
import mermaid from "mermaid";
import "highlight.js/styles/github-dark.css";
import hljs from 'highlight.js';

// Initialize mermaid
mermaid.initialize({
  startOnLoad: false,
  theme: 'dark',
  securityLevel: 'loose',
  fontFamily: 'monospace',
});

// A custom component to render a Mermaid diagram given the string.
const MermaidDiagram = ({ content }: { content: string }) => {
  const [diagram, setDiagram] = useState<string | boolean>(true);

  useEffect(() => {
    const render = async () => {
      try {
        // Generate a random ID for Mermaid to use.
        const id = `mermaid-svg-${Math.round(Math.random() * 10000000)}`;

        // Confirm the diagram is valid before rendering since it could be invalid
        // while streaming, or if the LLM "hallucinates" an invalid diagram.
        const isValid = await mermaid.parse(content, { suppressErrors: true });

        if (isValid) {
          const result = await mermaid.render(id, content);
          setDiagram(result.svg);

          // Apply any bind functions if they exist
          if (result.bindFunctions) {
            setTimeout(() => {
              const element = document.getElementById(`mermaid-diagram-${id}`);
              if (element && result.bindFunctions) {
                result.bindFunctions(element);
              }
            }, 0);
          }
        } else {
          setDiagram(false);
        }
      } catch (error) {
        console.error("Error rendering mermaid diagram:", error);
        setDiagram(false);
      }
    };
    render();
  }, [content]);

  if (diagram === true) {
    return <div className="p-4 text-center">Rendering diagram...</div>;
  } else if (diagram === false) {
    return <div className="p-4 text-red-500">Unable to render this diagram.</div>;
  } else {
    return (
      <div
        className="my-4 p-4 bg-slate-900 rounded-md overflow-auto max-w-full"
        dangerouslySetInnerHTML={{ __html: diagram ?? "" }}
      />
    );
  }
};

// Function to highlight code
const highlightCode = (code: string, language: string) => {
  try {
    if (language && hljs.getLanguage(language)) {
      return hljs.highlight(code, { language }).value;
    } else {
      return hljs.highlightAuto(code).value;
    }
  } catch (error) {
    console.error("Error highlighting code:", error);
    return code;
  }
};

export const useMarkdownProcessor = (content: string) => {
  // Initialize mermaid on component mount
  useEffect(() => {
    mermaid.initialize({
      startOnLoad: false,
      theme: "dark",
      securityLevel: 'loose',
      fontFamily: 'monospace',
    });
  }, []);

  return useMemo(() => {
    try {
      // Split content by lines to process
      const lines = content.split('\n');
      const result: React.ReactNode[] = [];

      // Process line by line
      for (let i = 0; i < lines.length; i++) {
        const line = lines[i];

        // Check for Mermaid code blocks
        if (line.trim().startsWith('```mermaid')) {
          // Find the end of the code block
          let mermaidContent = '';
          let j = i + 1;

          while (j < lines.length && !lines[j].trim().startsWith('```')) {
            mermaidContent += lines[j] + '\n';
            j++;
          }

          result.push(
            <MermaidDiagram key={`mermaid-${i}`} content={mermaidContent.trim()} />
          );

          // Skip to the end of the code block
          i = j;
          continue;
        }

        // Check for regular code blocks
        if (line.trim().startsWith('```')) {
          const language = line.trim().slice(3).trim();
          let codeContent = '';
          let j = i + 1;

          while (j < lines.length && !lines[j].trim().startsWith('```')) {
            codeContent += lines[j] + '\n';
            j++;
          }

          // Highlight the code
          const highlightedCode = highlightCode(codeContent.trim(), language);

          result.push(
            <div key={`code-${i}`} className="my-4 rounded-md overflow-hidden">
              <div className="bg-gray-800 px-4 py-2 text-xs font-mono">{language}</div>
              <pre className="p-4 bg-[#1E1E1E] overflow-x-auto">
                <code
                  dangerouslySetInnerHTML={{ __html: highlightedCode }}
                  className={`language-${language}`}
                />
              </pre>
            </div>
          );

          // Skip to the end of the code block
          i = j;
          continue;
        }

        // Process tables
        if (line.trim().startsWith('|') && line.trim().endsWith('|')) {
          // Check if we have a table header and separator
          if (i + 1 < lines.length && lines[i + 1].trim().startsWith('|') && lines[i + 1].trim().endsWith('|') &&
              lines[i + 1].includes('---')) {

            // This is a table - collect all table rows
            const tableRows: string[] = [line];
            let j = i + 1;

            while (j < lines.length && lines[j].trim().startsWith('|') && lines[j].trim().endsWith('|')) {
              tableRows.push(lines[j]);
              j++;
            }

            // Process the table
            const tableElement = processTable(tableRows);
            result.push(
              <div key={`table-${i}`} className="my-4 w-full overflow-auto">
                {tableElement}
              </div>
            );

            // Skip to after the table
            i = j - 1;
            continue;
          }
        }

        // Process headings
        if (line.trim().startsWith('#')) {
          const level = line.trim().match(/^#+/)?.[0].length || 1;
          const text = line.trim().replace(/^#+\s*/, '');

          if (level === 1) {
            result.push(<h1 key={`h-${i}`} className="text-2xl font-bold mt-6 mb-4">{text}</h1>);
          } else if (level === 2) {
            result.push(<h2 key={`h-${i}`} className="text-xl font-bold mt-5 mb-3">{text}</h2>);
          } else if (level === 3) {
            result.push(<h3 key={`h-${i}`} className="text-lg font-bold mt-4 mb-2">{text}</h3>);
          } else if (level === 4) {
            result.push(<h4 key={`h-${i}`} className="text-base font-bold mt-3 mb-2">{text}</h4>);
          } else if (level === 5) {
            result.push(<h5 key={`h-${i}`} className="text-sm font-bold mt-2 mb-1">{text}</h5>);
          } else if (level === 6) {
            result.push(<h6 key={`h-${i}`} className="text-xs font-bold mt-2 mb-1">{text}</h6>);
          }

          continue;
        }

        // Process blockquotes
        if (line.trim().startsWith('>')) {
          const text = line.trim().replace(/^>\s*/, '');
          result.push(
            <blockquote key={`quote-${i}`} className="border-l-4 border-primary pl-4 italic my-4">
              {text}
            </blockquote>
          );
          continue;
        }

        // Process lists (very basic)
        if (line.trim().match(/^[*-]\s/)) {
          const text = line.trim().replace(/^[*-]\s/, '');
          result.push(
            <ul key={`ul-${i}`} className="list-disc pl-6 mb-1">
              <li>{text}</li>
            </ul>
          );
          continue;
        }

        // Process ordered lists (very basic)
        if (line.trim().match(/^\d+\.\s/)) {
          const text = line.trim().replace(/^\d+\.\s/, '');
          result.push(
            <ol key={`ol-${i}`} className="list-decimal pl-6 mb-1">
              <li>{text}</li>
            </ol>
          );
          continue;
        }

        // Process horizontal rules
        if (line.trim().match(/^---+$/)) {
          result.push(<hr key={`hr-${i}`} className="my-6 border-t border-border" />);
          continue;
        }

        // Process inline formatting (bold, italic, code)
        let text = line;

        // Bold
        text = text.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

        // Italic
        text = text.replace(/\*([^*]+)\*/g, '<em>$1</em>');

        // Inline code
        text = text.replace(/`([^`]+)`/g, '<code class="rounded-sm px-1 py-0.5 font-mono text-sm bg-muted">$1</code>');

        // Links
        text = text.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noreferrer" class="text-primary underline">$1</a>');

        // Add the processed line
        if (text.trim()) {
          result.push(
            <div key={`p-${i}`} className="mb-4 last:mb-0 leading-relaxed" dangerouslySetInnerHTML={{ __html: text }} />
          );
        } else if (i > 0 && lines[i-1].trim()) {
          // Add an empty line if the previous line was not empty
          result.push(<div key={`empty-${i}`} className="h-4" />);
        }
      }

      return <>{result}</>;
    } catch (error) {
      console.error("Error processing markdown:", error);
      return <div className="text-red-500">Error rendering markdown content</div>;
    }
  }, [content]);
};

// Function to process a table from markdown
const processTable = (tableRows: string[]): React.ReactNode => {
  // First row is header, second is separator, rest are data
  const headerRow = tableRows[0];
  const dataRows = tableRows.slice(2);

  // Process header cells
  const headerCells = headerRow
    .trim()
    .slice(1, -1) // Remove the outer | characters
    .split('|')
    .map(cell => cell.trim());

  // Process data rows
  const processedDataRows = dataRows.map(row => {
    return row
      .trim()
      .slice(1, -1) // Remove the outer | characters
      .split('|')
      .map(cell => cell.trim());
  });

  return (
    <table className="w-full border-collapse border border-border">
      <thead className="bg-muted">
        <tr>
          {headerCells.map((cell, index) => (
            <th key={index} className="border border-border px-4 py-2 text-left font-bold">
              {cell}
            </th>
          ))}
        </tr>
      </thead>
      <tbody>
        {processedDataRows.map((row, rowIndex) => (
          <tr key={rowIndex}>
            {row.map((cell, cellIndex) => (
              <td key={cellIndex} className="border border-border px-4 py-2">
                {cell}
              </td>
            ))}
          </tr>
        ))}
      </tbody>
    </table>
  );
};
