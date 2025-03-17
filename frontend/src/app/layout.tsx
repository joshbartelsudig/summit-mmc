import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import 'highlight.js/styles/atom-one-dark.css'
import { ThemeProvider } from '@/components/theme-provider'
import { Header } from '@/components/header'
import { cn } from '@/lib/utils'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'Multi-Model Chat',
  description: 'Chat with Azure OpenAI and Amazon Bedrock models',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head />
      <body
        className={cn(
          "min-h-screen bg-background font-sans antialiased",
          inter.className
        )}
      >
        <ThemeProvider
          attribute="class"
          defaultTheme="light"
          enableSystem
          disableTransitionOnChange
        >
          <div className="flex flex-col h-screen">
            <Header />
            {children}
          </div>
        </ThemeProvider>
      </body>
    </html>
  )
}
