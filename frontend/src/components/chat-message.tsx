'use client'

import React, { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { cn } from '@/lib/utils'
import { MarkdownRenderer } from './markdown-renderer'
import { Message } from '@/types'
import { User, Bot, Check, Copy, Edit, RefreshCw, Trash, Loader2 } from 'lucide-react'

type ChatMessageProps = {
  message: Message
  isLastMessage?: boolean
  isLoading?: boolean
  onRetry?: () => void
  onEdit?: () => void
  onDelete?: () => void
  isEditing?: boolean
  editedContent?: string
  setEditedContent?: (content: string) => void
  onSaveEdit?: () => void
  onCancelEdit?: () => void
  className?: string
}

export function ChatMessage({
  message,
  isLastMessage,
  isLoading,
  onRetry,
  onEdit,
  onDelete,
  isEditing,
  editedContent,
  setEditedContent,
  onSaveEdit,
  onCancelEdit,
  className,
  ...props
}: ChatMessageProps) {
  const { role, content, name } = message;
  const [showCopied, setShowCopied] = useState(false);

  const handleCopy = () => {
    if (!content) return;
    navigator.clipboard.writeText(content);
    setShowCopied(true);
    setTimeout(() => setShowCopied(false), 2000);
  };

  return (
    <div
      className={cn(
        "group relative mb-4 flex items-start md:mb-6",
        className
      )}
      {...props}
    >
      <div
        className={cn(
          "flex size-8 shrink-0 select-none items-center justify-center rounded-md border shadow",
          role === "user"
            ? "bg-background"
            : "bg-primary text-primary-foreground"
        )}
      >
        {role === "user" ? <User className="size-4" /> : <Bot className="size-4" />}
      </div>
      <div className="ml-4 flex-1 space-y-2 overflow-hidden px-1">
        <div className="text-sm font-medium">
          {role === "user" ? "You" : name || "Assistant"}
        </div>
        {isEditing ? (
          <div className="space-y-2">
            <Textarea
              value={editedContent}
              onChange={(e) => setEditedContent?.(e.target.value)}
              className="mt-2 w-full resize-none"
              rows={5}
            />
            <div className="flex justify-end space-x-2">
              <Button size="sm" variant="outline" onClick={onCancelEdit}>
                Cancel
              </Button>
              <Button size="sm" onClick={onSaveEdit}>
                Save
              </Button>
            </div>
          </div>
        ) : (
          <div className="prose prose-sm dark:prose-invert max-w-none space-y-2">
            {content ? (
              <div className="markdown-content prose prose-sm dark:prose-invert max-w-none">
                <MarkdownRenderer content={content} />
              </div>
            ) : (
              <div className="h-4" />
            )}
            {isLoading && isLastMessage && (
              <div className="flex items-center space-x-2">
                <Loader2 className="size-4" />
                <span className="text-sm text-muted-foreground">
                  Thinking...
                </span>
              </div>
            )}
          </div>
        )}
        {!isEditing && (
          <div className="flex items-center space-x-2">
            <div className="flex items-center">
              <Button
                variant="ghost"
                size="icon"
                className="size-8 opacity-0 transition-opacity group-hover:opacity-100"
                onClick={handleCopy}
              >
                {showCopied ? (
                  <Check className="size-4" />
                ) : (
                  <Copy className="size-4" />
                )}
                <span className="sr-only">Copy message</span>
              </Button>
            </div>
            {role === "user" && onEdit && (
              <div className="flex items-center">
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8 opacity-0 transition-opacity group-hover:opacity-100"
                  onClick={onEdit}
                >
                  <Edit className="size-4" />
                  <span className="sr-only">Edit message</span>
                </Button>
              </div>
            )}
            {role === "assistant" && isLastMessage && onRetry && (
              <div className="flex items-center">
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8 opacity-0 transition-opacity group-hover:opacity-100"
                  onClick={onRetry}
                >
                  <RefreshCw className="size-4" />
                  <span className="sr-only">Retry</span>
                </Button>
              </div>
            )}
            {onDelete && (
              <div className="flex items-center">
                <Button
                  variant="ghost"
                  size="icon"
                  className="size-8 opacity-0 transition-opacity group-hover:opacity-100"
                  onClick={onDelete}
                >
                  <Trash className="size-4" />
                  <span className="sr-only">Delete message</span>
                </Button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
