"use client"

import { useState, useRef } from "react"
import { Clock, Search, Trash2, Plus } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { cn } from "@/lib/utils"
import { ChatSession } from "@/types"

type ChatHistoryProps = {
  sessions: ChatSession[]
  onSelectSession: (sessionId: string) => void
  onDeleteSession: (sessionId: string) => void
  onNewChat: () => void
  selectedSessionId: string | null
}

export function ChatHistory({
  sessions,
  onSelectSession,
  onDeleteSession,
  onNewChat,
  selectedSessionId,
}: ChatHistoryProps) {
  const [searchQuery, setSearchQuery] = useState("")

  // Filter sessions based on search query
  const filteredSessions = sessions.filter((session) =>
    session.title.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="flex flex-col h-full">
      <div className="p-3">
        <Button
          onClick={onNewChat}
          variant="outline"
          className="w-full flex items-center justify-start gap-2 py-2"
          size="sm"
        >
          <Plus className="h-4 w-4" />
          New Chat
        </Button>
      </div>

      <div className="px-3 pb-2">
        <div className="relative">
          <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search conversations..."
            className="pl-8 h-9 text-xs"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
          />
        </div>
      </div>

      <div className="flex-1 overflow-auto">
        <div className="px-1">
          {filteredSessions.length > 0 ? (
            filteredSessions.map((session) => (
              <div
                key={session.id}
                className={cn(
                  "flex flex-col px-2 py-2 text-sm hover:bg-accent/50 relative group cursor-pointer",
                  selectedSessionId === session.id && "bg-accent"
                )}
                onClick={() => onSelectSession(session.id)}
              >
                <div className="font-medium text-xs">{session.title}</div>
                <div className="flex items-center text-xs text-muted-foreground mt-1">
                  <Clock className="mr-1 h-3 w-3" />
                  {new Date(session.date).toLocaleDateString()}

                  <Button
                    variant="ghost"
                    size="icon"
                    className="h-6 w-6 ml-auto opacity-0 group-hover:opacity-100 transition-opacity"
                    onClick={(e) => {
                      e.stopPropagation()
                      onDeleteSession(session.id)
                    }}
                  >
                    <Trash2 className="h-3 w-3 text-muted-foreground" />
                  </Button>
                </div>
              </div>
            ))
          ) : (
            <div className="p-4 text-center text-xs text-muted-foreground">
              {searchQuery ? "No conversations found" : "No conversations yet"}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}
