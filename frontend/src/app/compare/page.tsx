'use client'

import { useState, useEffect } from 'react'
import { Send, ChevronDown, Maximize2, Minimize2, Copy, Check } from 'lucide-react'
import { Send, ChevronDown, Maximize2, Minimize2, Copy, Check } from 'lucide-react'

import { Input } from '@/components/ui/input'
import { ModelSelector } from '@/components/model-selector'
import { MarkdownRenderer } from '@/components/markdown-renderer'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Message, ModelInfo } from '@/types'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from '@/components/ui/dropdown-menu'
import { Tabs, TabsList, TabsTrigger } from '@/components/ui/tabs'

// Default prompts categorized by type
const DEFAULT_PROMPTS = {
  analytical: [
    "Explain the concept of quantum computing and its potential impact on cryptography",
    "Analyze the pros and cons of renewable energy versus fossil fuels",
    "What are the ethical considerations in artificial intelligence development?",
    "Compare and contrast different approaches to climate change mitigation",
    "Explain how blockchain technology works and its real-world applications"
  ],
  creative: [
    "Write a short story about a robot discovering emotions",
    "Create a poem about the changing seasons",
    "Describe an alien civilization that evolved underwater",
    "Write a dialogue between a time traveler from 1800 and someone from 2025",
    "Invent a new sport that could be played in zero gravity"
  ],
  technical: [
    "Explain how to implement a binary search tree in Python",
    "What are the key differences between REST and GraphQL APIs?",
    "Describe the process of training a neural network for image recognition",
    "How would you optimize a database query that's running slowly?",
    "Explain the concept of containerization and how Docker works"
  ],
  reasoning: [
    "Solve this logical puzzle: Three people check into a hotel room that costs $30. They each pay $10. Later, the hotel manager realizes the room was only supposed to cost $25, so he gives $5 to the bellhop to return to the guests. The bellhop decides to keep $2 and gives $1 back to each guest. Now each guest has paid $9, for a total of $27. The bellhop has $2. That's $29. Where is the missing dollar?",
    "What would happen if gravity suddenly became twice as strong?",
    "Design an experiment to test whether plants respond to music",
    "How would you determine if a coin is fair or biased?",
    "What are the implications of discovering extraterrestrial life?"
  ]
};

// Recommended model pairings based on available models
const RECOMMENDED_PAIRINGS = [
  { name: "GPT-4o vs Claude 3.7 Sonnet", models: ["gpt-4o", "anthropic.claude-3-7-sonnet-20250219-v1:0"] },
  { name: "Claude 3.7 Sonnet vs Llama 3.3 70B", models: ["anthropic.claude-3-7-sonnet-20250219-v1:0", "meta.llama3-3-70b-instruct-v1:0"] },
  { name: "Claude 3.5 Sonnet vs Claude 3.5 Haiku", models: ["anthropic.claude-3-5-sonnet-20241022-v2:0", "anthropic.claude-3-5-haiku-20241022-v1:0"] },
  { name: "Mistral 7B vs Titan Text Premier", models: ["mistral.mistral-7b-instruct-v0:2", "amazon.titan-text-premier-v1:0"] },
  { name: "GPT-3.5 Turbo vs GPT-4o", models: ["gpt-35-turbo", "gpt-4o"] },
  { name: "Titan Text Premier vs Titan Text Lite", models: ["amazon.titan-text-premier-v1:0", "amazon.titan-text-lite-v1"] }
];

export default function ComparePage() {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [models, setModels] = useState<ModelInfo[]>([])
  const [selectedModelA, setSelectedModelA] = useState<ModelInfo | null>(null)
  const [selectedModelB, setSelectedModelB] = useState<ModelInfo | null>(null)
  const [models, setModels] = useState<ModelInfo[]>([])
  const [selectedModelA, setSelectedModelA] = useState<ModelInfo | null>(null)
  const [selectedModelB, setSelectedModelB] = useState<ModelInfo | null>(null)
  const [responseA, setResponseA] = useState<Message | null>(null)
  const [responseB, setResponseB] = useState<Message | null>(null)
  const [activePromptCategory, setActivePromptCategory] = useState('analytical')
  const [selectedPairing, setSelectedPairing] = useState<typeof RECOMMENDED_PAIRINGS[0] | null>(null)
  const [fullscreenMode, setFullscreenMode] = useState<'none' | 'a' | 'b'>('none')
  const [copyStatusA, setCopyStatusA] = useState(false)
  const [copyStatusB, setCopyStatusB] = useState(false)

  // Reset copy status after delay
  useEffect(() => {
    if (copyStatusA) {
      const timer = setTimeout(() => setCopyStatusA(false), 2000)
      return () => clearTimeout(timer)
    }
  }, [copyStatusA])

  useEffect(() => {
    if (copyStatusB) {
      const timer = setTimeout(() => setCopyStatusB(false), 2000)
      return () => clearTimeout(timer)
    }
  }, [copyStatusB])

  // Copy response content to clipboard
  const copyToClipboard = async (content: string, isModelA: boolean) => {
    try {
      await navigator.clipboard.writeText(content)
      if (isModelA) {
        setCopyStatusA(true)
      } else {
        setCopyStatusB(true)
      }
    } catch (err) {
      console.error('Failed to copy text: ', err)
    }
  }
  const [activePromptCategory, setActivePromptCategory] = useState('analytical')
  const [selectedPairing, setSelectedPairing] = useState<typeof RECOMMENDED_PAIRINGS[0] | null>(null)
  const [fullscreenMode, setFullscreenMode] = useState<'none' | 'a' | 'b'>('none')
  const [copyStatusA, setCopyStatusA] = useState(false)
  const [copyStatusB, setCopyStatusB] = useState(false)

  // Reset copy status after delay
  useEffect(() => {
    if (copyStatusA) {
      const timer = setTimeout(() => setCopyStatusA(false), 2000)
      return () => clearTimeout(timer)
    }
  }, [copyStatusA])

  useEffect(() => {
    if (copyStatusB) {
      const timer = setTimeout(() => setCopyStatusB(false), 2000)
      return () => clearTimeout(timer)
    }
  }, [copyStatusB])

  // Copy response content to clipboard
  const copyToClipboard = async (content: string, isModelA: boolean) => {
    try {
      await navigator.clipboard.writeText(content)
      if (isModelA) {
        setCopyStatusA(true)
      } else {
        setCopyStatusB(true)
      }
    } catch (err) {
      console.error('Failed to copy text: ', err)
    }
  }

  // Fetch models from the backend API
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/models')
        if (!response.ok) {
          throw new Error('Failed to fetch models')
        }
        const data = await response.json()
        const modelsList = data.models || []
        setModels(modelsList)

        // Set default models if available
        if (modelsList.length > 0) {
          setSelectedModelA(modelsList[0])
          if (modelsList.length > 1) {
            setSelectedModelB(modelsList[1])
          }
        }
      } catch (error) {
        console.error('Error fetching models:', error)
      }
    }

    fetchModels()
  }, [])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !selectedModelA || !selectedModelB || isLoading) return

    setIsLoading(true)
    setResponseA(null)
    setResponseB(null)

    const userMessage: Message = {
      role: 'user',
      content: input
    }

    try {
      // Send request to model A
      const responseA = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [userMessage],
          model: selectedModelA.id,
          stream: false,
          store_in_session: false
          store_in_session: false
        }),
      })

      if (!responseA.ok) {
        throw new Error(`Error from model A: ${responseA.statusText}`)
      }

      const dataA = await responseA.json()
      setResponseA({
        role: 'assistant',
        content: dataA.choices[0].message.content
      })

      // Send request to model B
      const responseB = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [userMessage],
          model: selectedModelB.id,
          stream: false,
          store_in_session: false
          store_in_session: false
        }),
      })

      if (!responseB.ok) {
        throw new Error(`Error from model B: ${responseB.statusText}`)
      }

      const dataB = await responseB.json()
      setResponseB({
        role: 'assistant',
        content: dataB.choices[0].message.content
      })
    } catch (error) {
      console.error('Error sending message:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Handle manual model selection
  const handleModelASelect = (model: ModelInfo) => {
    setSelectedModelA(model)
    // Clear selected pairing if model is changed manually
    setSelectedPairing(null)
  }

  const handleModelBSelect = (model: ModelInfo) => {
    setSelectedModelB(model)
    // Clear selected pairing if model is changed manually
    setSelectedPairing(null)
  }

  // Set a prompt from the default prompts
  const setDefaultPrompt = (prompt: string) => {
    setInput(prompt)
  }

  // Set a recommended model pairing
  const setRecommendedPairing = (pairing: typeof RECOMMENDED_PAIRINGS[0]) => {
    const modelA = models.find(m => m.id === pairing.models[0]) || null
    const modelB = models.find(m => m.id === pairing.models[1]) || null

    if (modelA) setSelectedModelA(modelA)
    if (modelB) setSelectedModelB(modelB)
    setSelectedPairing(pairing)
  }

  return (
    <div className="container h-full flex flex-col overflow-hidden py-6">
      <h2 className="text-2xl font-semibold mb-6">Compare Model Responses</h2>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
        {/* Left column: Model selectors */}
        <div className="space-y-4">
          <Card className="shadow-sm">
            <CardHeader className="p-3 pb-0">
              <CardTitle className="text-lg flex justify-between items-center">
                <span>Models</span>
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button variant="outline" size="sm" className="h-8 text-xs">
                      Recommended <ChevronDown className="ml-1 h-3 w-3" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="end">
                    {RECOMMENDED_PAIRINGS.map((pairing, index) => (
                      <DropdownMenuItem key={index} onClick={() => setRecommendedPairing(pairing)}>
                        {selectedPairing && selectedPairing.name === pairing.name ? (
                          <span className="text-blue-500">{pairing.name}</span>
                        ) : (
                          pairing.name
                        )}
                      </DropdownMenuItem>
                    ))}
                  </DropdownMenuContent>
                </DropdownMenu>
              </CardTitle>
            </CardHeader>
            <CardContent className="p-3 pt-2 space-y-3">
              <div>
                <h3 className="text-xs font-medium mb-1">Model A</h3>
                <ModelSelector
                  models={models}
                  selectedModel={selectedModelA}
                  onModelSelect={handleModelASelect}
                />
              </div>

              <div>
                <h3 className="text-xs font-medium mb-1">Model B</h3>
                <ModelSelector
                  models={models}
                  selectedModel={selectedModelB}
                  onModelSelect={handleModelBSelect}
                />
              </div>
            </CardContent>
          </Card>
        </div>

        {/* Right columns: Prompt selection */}
        <div className="md:col-span-2">
          <Card className="shadow-sm h-full">
            <CardHeader className="p-3 flex flex-row items-center justify-between">
              <CardTitle className="text-lg">Prompt</CardTitle>
              <Tabs value={activePromptCategory} onValueChange={setActivePromptCategory} className="w-auto">
                <TabsList className="grid grid-cols-4">
                  <TabsTrigger value="analytical" className="px-3 py-1 text-xs">Analytical</TabsTrigger>
                  <TabsTrigger value="creative" className="px-3 py-1 text-xs">Creative</TabsTrigger>
                  <TabsTrigger value="technical" className="px-3 py-1 text-xs">Technical</TabsTrigger>
                  <TabsTrigger value="reasoning" className="px-3 py-1 text-xs">Reasoning</TabsTrigger>
                </TabsList>
              </Tabs>
            </CardHeader>
            <CardContent className="p-3 space-y-4">
              <div className="grid grid-cols-1 gap-2 mb-4 max-h-[200px] overflow-y-auto">
                {DEFAULT_PROMPTS[activePromptCategory as keyof typeof DEFAULT_PROMPTS].map((prompt, index) => (
                  <Button
                    key={index}
                    variant="outline"
                    className="justify-start h-auto py-1.5 px-3 text-left text-xs"
                    onClick={() => setDefaultPrompt(prompt)}
                  >
                    {prompt.length > 80 ? prompt.substring(0, 80) + '...' : prompt}
                  </Button>
                ))}
              </div>

              <form onSubmit={handleSubmit} className="flex w-full items-center space-x-2">
                <Input
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Enter your prompt here..."
                  className="flex-1"
                />
                <Button
                  type="submit"
                  size="icon"
                  disabled={isLoading || !input.trim() || !selectedModelA || !selectedModelB}
                >
                  <Send className="h-4 w-4" />
                  <span className="sr-only">Send</span>
                </Button>
              </form>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Bottom section: Model responses */}
      {/* Bottom section: Model responses */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6 overflow-y-auto pb-6">
        {fullscreenMode === 'none' || fullscreenMode === 'a' ? (
          <Card className={`shadow-sm h-full ${fullscreenMode === 'a' ? 'md:col-span-2' : ''}`}>
            <CardHeader className="p-2 sticky top-0 bg-card z-10 flex flex-row justify-between items-center">
              <CardTitle className="text-sm">
                {selectedModelA ? selectedModelA.name : 'Model A'} Response
              </CardTitle>
              <div className="flex space-x-1">
                {responseA && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(responseA.content, true)}
                    className="h-7 w-7 p-0"
                    disabled={copyStatusA}
                  >
                    {copyStatusA ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setFullscreenMode(fullscreenMode === 'a' ? 'none' : 'a')}
                  className="h-7 w-7 p-0"
                >
                  {fullscreenMode === 'a' ? <Minimize2 className="h-3 w-3" /> : <Maximize2 className="h-3 w-3" />}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-3 overflow-auto max-h-[calc(100vh-20rem)]">
              {isLoading ? (
                <div className="flex justify-center items-center h-64">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                </div>
              ) : responseA ? (
                <div className="prose max-w-none prose-sm">
                  <MarkdownRenderer content={responseA.content} />
                </div>
              ) : (
                <div className="text-center text-gray-500 h-64 flex items-center justify-center">
                  <p>Response will appear here</p>
                </div>
              )}
            </CardContent>
          </Card>
        ) : null}

        {fullscreenMode === 'none' || fullscreenMode === 'b' ? (
          <Card className={`shadow-sm h-full ${fullscreenMode === 'b' ? 'md:col-span-2' : ''}`}>
            <CardHeader className="p-2 sticky top-0 bg-card z-10 flex flex-row justify-between items-center">
              <CardTitle className="text-sm">
                {selectedModelB ? selectedModelB.name : 'Model B'} Response
              </CardTitle>
              <div className="flex space-x-1">
                {responseB && (
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => copyToClipboard(responseB.content, false)}
                    className="h-7 w-7 p-0"
                    disabled={copyStatusB}
                  >
                    {copyStatusB ? <Check className="h-3 w-3 text-green-500" /> : <Copy className="h-3 w-3" />}
                  </Button>
                )}
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={() => setFullscreenMode(fullscreenMode === 'b' ? 'none' : 'b')}
                  className="h-7 w-7 p-0"
                >
                  {fullscreenMode === 'b' ? <Minimize2 className="h-3 w-3" /> : <Maximize2 className="h-3 w-3" />}
                </Button>
              </div>
            </CardHeader>
            <CardContent className="p-3 overflow-auto max-h-[calc(100vh-20rem)]">
              {isLoading ? (
                <div className="flex justify-center items-center h-64">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                </div>
              ) : responseB ? (
                <div className="prose max-w-none prose-sm">
                  <MarkdownRenderer content={responseB.content} />
                </div>
              ) : (
                <div className="text-center text-gray-500 h-64 flex items-center justify-center">
                  <p>Response will appear here</p>
                </div>
              )}
            </CardContent>
          </Card>
        ) : null}
      </div>
    </div>
  )
}
