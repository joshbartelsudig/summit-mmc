"use client"

import * as React from "react"
import { Check, ChevronsUpDown, RefreshCw } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { SystemPromptSettings } from '@/components/system-prompt-settings'
import {
  Popover,
  PopoverContent,
  PopoverTrigger,
} from "@/components/ui/popover"
import { ModelInfo } from "@/types"

interface ModelSelectorProps {
  selectedModel: ModelInfo | null
  onModelSelect: (model: ModelInfo) => void
  models?: ModelInfo[]
  onSystemPromptChange?: (prompt: string | null) => void
}

export function ModelSelector({
  selectedModel,
  onModelSelect,
  models: propModels,
  onSystemPromptChange,
}: ModelSelectorProps) {
  const [open, setOpen] = React.useState(false)
  const [models, setModels] = React.useState<ModelInfo[]>(propModels || [])
  const [loading, setLoading] = React.useState(!propModels)
  const [refreshing, setRefreshing] = React.useState(false)

  // Fetch models from API
  const fetchModels = async (refresh = false) => {
    try {
      setLoading(true)
      const url = 'http://localhost:8000/api/v1/models' + (refresh ? '?refresh=true' : '')
      
      const response = await fetch(url)
      if (!response.ok) {
        throw new Error('Failed to fetch models')
      }
      
      const data = await response.json()
      setModels(data.models || [])
    } catch (error) {
      console.error('Error fetching models:', error)
      // Fallback to default models if API call fails
      setModels([
        {
          id: "gpt-35-turbo",
          name: "GPT-3.5 Turbo",
          provider: "azure"
        },
        {
          id: "gpt-4",
          name: "GPT-4",
          provider: "azure"
        },
        {
          id: "anthropic.claude-v2",
          name: "Claude V2",
          provider: "bedrock"
        },
        {
          id: "anthropic.claude-instant-v1",
          name: "Claude Instant",
          provider: "bedrock"
        }
      ])
    } finally {
      setLoading(false)
      setRefreshing(false)
    }
  }
  
  // Initial fetch on component mount if models not provided as props
  React.useEffect(() => {
    // Always fetch models on mount, the backend will use cache if available
    fetchModels()
  }, [])
  
  // Handle refresh button click
  const handleRefresh = async () => {
    setRefreshing(true)
    await fetchModels(true)
  }

  // Group models by provider
  const azureModels = models.filter(model => model.provider === "azure")
  const bedrockModels = models.filter(model => model.provider === "bedrock")

  return (
    <div className="flex items-center gap-2">
      <Popover open={open} onOpenChange={setOpen}>
        <PopoverTrigger asChild>
          <Button
            variant="outline"
            role="combobox"
            aria-expanded={open}
            className="w-[250px] justify-between h-8 text-xs"
            disabled={loading}
            size="sm"
          >
            {loading ? "Loading models..." : (selectedModel ? selectedModel.name : "Select model...")}
            <ChevronsUpDown className="ml-2 h-3 w-3 shrink-0 opacity-50" />
          </Button>
        </PopoverTrigger>
        <PopoverContent className="w-[250px] p-2">
          <div className="space-y-4">
            {azureModels.length > 0 && (
              <div>
                <h4 className="mb-2 text-xs font-medium">Azure OpenAI</h4>
                <div className="space-y-1">
                  {azureModels.map((model) => (
                    <Button
                      key={model.id}
                      variant="ghost"
                      size="sm"
                      className="w-full justify-start text-xs h-7"
                      onClick={() => {
                        onModelSelect(model)
                        setOpen(false)
                      }}
                    >
                      <Check
                        className={cn(
                          "mr-2 h-3 w-3",
                          selectedModel?.id === model.id ? "opacity-100" : "opacity-0"
                        )}
                      />
                      {model.name}
                    </Button>
                  ))}
                </div>
              </div>
            )}
            {bedrockModels.length > 0 && (
              <div>
                <h4 className="mb-2 text-xs font-medium">Amazon Bedrock</h4>
                <div className="space-y-1">
                  {bedrockModels.map((model) => (
                    <Button
                      key={model.id}
                      variant="ghost"
                      size="sm"
                      className="w-full justify-start text-xs h-7"
                      onClick={() => {
                        onModelSelect(model)
                        setOpen(false)
                      }}
                    >
                      <Check
                        className={cn(
                          "mr-2 h-3 w-3",
                          selectedModel?.id === model.id ? "opacity-100" : "opacity-0"
                        )}
                      />
                      {model.name}
                    </Button>
                  ))}
                </div>
              </div>
            )}
          </div>
        </PopoverContent>
      </Popover>
      <Button 
        variant="ghost" 
        size="icon" 
        className="h-8 w-8"
        onClick={handleRefresh} 
        disabled={refreshing || loading}
      >
        <RefreshCw className={cn("h-3 w-3", refreshing && "animate-spin")} />
        <span className="sr-only">Refresh models</span>
      </Button>
      {onSystemPromptChange && <SystemPromptSettings onSystemPromptChange={onSystemPromptChange} />}
    </div>
  )
}
