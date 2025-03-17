"use client"

import Link from 'next/link'
import { ThemeToggle } from '@/components/theme-toggle'
import { LayoutGrid, MessagesSquare } from 'lucide-react'
import { cn } from '@/lib/utils'
import { usePathname } from 'next/navigation'

export function Header() {
  const pathname = usePathname()

  return (
    <header className="border-b">
      <div className="flex h-12 items-center px-4 justify-between">
        <div className="flex items-center">
          <div className="flex items-center gap-2 mr-4">
            <LayoutGrid className="h-5 w-5" />
            <Link href="/" className="text-sm font-semibold">
              Multi-Model Chat
            </Link>
          </div>
          <nav className="flex items-center space-x-2">
            <Link
              href="/"
              className={cn(
                "text-xs font-medium transition-colors hover:text-primary px-2 py-1",
                pathname === "/" ? "text-primary bg-accent rounded" : "text-muted-foreground"
              )}
            >
              <div className="flex items-center gap-1">
                <MessagesSquare className="h-3 w-3" />
                <span>Chat</span>
              </div>
            </Link>
            <Link
              href="/compare"
              className={cn(
                "text-xs font-medium transition-colors hover:text-primary px-2 py-1",
                pathname === "/compare" ? "text-primary bg-accent rounded" : "text-muted-foreground"
              )}
            >
              <div className="flex items-center gap-1">
                <svg
                  xmlns="http://www.w3.org/2000/svg"
                  width="12"
                  height="12"
                  viewBox="0 0 24 24"
                  fill="none"
                  stroke="currentColor"
                  strokeWidth="2"
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  className="h-3 w-3"
                >
                  <path d="M18 6H5a2 2 0 0 0-2 2v3a2 2 0 0 0 2 2h13l4-3.5L18 6Z"></path>
                  <path d="M12 13v9"></path>
                  <path d="M5 13v9"></path>
                  <path d="M5 2v4"></path>
                  <path d="M18 2v4"></path>
                </svg>
                <span>Compare</span>
              </div>
            </Link>
          </nav>
        </div>
        <div className="flex items-center space-x-2">
          <ThemeToggle />
        </div>
      </div>
    </header>
  )
}
