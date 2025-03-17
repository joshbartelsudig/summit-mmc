"use client"

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { Textarea } from '@/components/ui/textarea'
import { Settings2 } from 'lucide-react'
import { toast } from 'sonner'

interface SystemPromptSettingsProps {
  onSystemPromptChange: (prompt: string | null) => void
}

export function SystemPromptSettings({ onSystemPromptChange }: SystemPromptSettingsProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [customPrompt, setCustomPrompt] = useState<string>('')
  const [isUsingCustomPrompt, setIsUsingCustomPrompt] = useState(false)

  const handleSave = () => {
    if (isUsingCustomPrompt && !customPrompt.trim()) {
      toast.error('Custom prompt cannot be empty')
      return
    }
    onSystemPromptChange(isUsingCustomPrompt ? customPrompt : null)
    setIsOpen(false)
    toast.success('System prompt settings saved')
  }

  const handleReset = () => {
    setIsUsingCustomPrompt(false)
    setCustomPrompt('')
    onSystemPromptChange(null)
    setIsOpen(false)
    toast.success('System prompt reset to default')
  }

  return (
    <Popover open={isOpen} onOpenChange={setIsOpen}>
      <PopoverTrigger asChild>
        <Button variant="ghost" size="icon" title="System Prompt Settings">
          <Settings2 className="h-4 w-4" />
          <span className="sr-only">System Prompt Settings</span>
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-[400px] p-4" align="end">
        <div className="space-y-4">
          <div className="flex items-center space-x-2">
            <input
              type="checkbox"
              id="useCustomPrompt"
              checked={isUsingCustomPrompt}
              onChange={(e) => setIsUsingCustomPrompt(e.target.checked)}
              className="h-4 w-4"
            />
            <label htmlFor="useCustomPrompt">Use Custom System Prompt</label>
          </div>
          {isUsingCustomPrompt && (
            <Textarea
              placeholder="Enter your custom system prompt..."
              value={customPrompt}
              onChange={(e) => setCustomPrompt(e.target.value)}
              className="min-h-[200px]"
            />
          )}
          <div className="flex justify-end space-x-2">
            <Button variant="outline" onClick={handleReset}>
              Reset to Default
            </Button>
            <Button onClick={handleSave}>Save</Button>
          </div>
        </div>
      </PopoverContent>
    </Popover>
  )
}
