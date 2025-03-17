'use client'

import { useState, useEffect, useRef } from 'react'
import { Send } from 'lucide-react'

import { Input } from '@/components/ui/input'
import { ModelSelector } from '@/components/model-selector'
import { MarkdownRenderer } from '@/components/markdown-renderer'
import { Button } from '@/components/ui/button'
import { Textarea } from '@/components/ui/textarea'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs'
import { Message, ModelInfo } from '@/types'
import { Toaster } from '@/components/ui/sonner'
import { toast } from 'sonner'

// Default system prompts for each model in the chain
const DEFAULT_SYSTEM_PROMPTS = {
  model1: `You are a helpful assistant that specializes in analyzing and structuring information.
Your task is to analyze the user's input and provide a structured response that will be passed to another AI.
Focus on extracting key information, organizing it clearly, and highlighting important aspects.`,
  
  model2: `You are a helpful assistant that specializes in creative and detailed responses.
You will receive structured information from another AI and your task is to expand upon it,
adding depth, nuance, and creative elements while maintaining accuracy.
Provide a comprehensive and well-formatted response to the user's original query.`
}

export default function ChainPage() {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [models, setModels] = useState<ModelInfo[]>([])
  const [selectedModel1, setSelectedModel1] = useState<ModelInfo | null>(null)
  const [selectedModel2, setSelectedModel2] = useState<ModelInfo | null>(null)
  const [intermediateResponse, setIntermediateResponse] = useState<Message | null>(null)
  const [finalResponse, setFinalResponse] = useState<Message | null>(null)
  const [systemPrompt1, setSystemPrompt1] = useState(DEFAULT_SYSTEM_PROMPTS.model1)
  const [systemPrompt2, setSystemPrompt2] = useState(DEFAULT_SYSTEM_PROMPTS.model2)
  const [activeTab, setActiveTab] = useState('config')
  const messagesEndRef = useRef<HTMLDivElement>(null)

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
          setSelectedModel1(modelsList[0])
          if (modelsList.length > 1) {
            setSelectedModel2(modelsList[1])
          } else {
            setSelectedModel2(modelsList[0])
          }
        }
      } catch (error) {
        console.error('Error fetching models:', error)
        toast.error('Failed to fetch available models')
      }
    }

    fetchModels()
  }, [])

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [intermediateResponse, finalResponse])

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim() || !selectedModel1 || !selectedModel2 || isLoading) return

    setIsLoading(true)
    setIntermediateResponse(null)
    setFinalResponse(null)
    setActiveTab('results')

    const userMessage: Message = {
      role: 'user',
      content: input
    }

    try {
      // First model call
      const response1 = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [userMessage],
          model: selectedModel1.id,
          stream: false,
          system_prompt: systemPrompt1
        }),
      })

      if (!response1.ok) {
        throw new Error(`Error from first model: ${response1.statusText}`)
      }

      const data1 = await response1.json()
      const intermediateContent = data1.choices[0].message.content
      
      setIntermediateResponse({
        role: 'assistant',
        content: intermediateContent
      })

      // Second model call with the output from the first model
      const response2 = await fetch('http://localhost:8000/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [
            userMessage,
            {
              role: 'assistant',
              content: `First model analysis: ${intermediateContent}`
            }
          ],
          model: selectedModel2.id,
          stream: false,
          system_prompt: systemPrompt2
        }),
      })

      if (!response2.ok) {
        throw new Error(`Error from second model: ${response2.statusText}`)
      }

      const data2 = await response2.json()
      setFinalResponse({
        role: 'assistant',
        content: data2.choices[0].message.content
      })
    } catch (error) {
      console.error('Error in model chain:', error)
      toast.error('Error in model chain: ' + (error instanceof Error ? error.message : 'Unknown error'))
    } finally {
      setIsLoading(false)
    }
  }

  const resetSystemPrompts = () => {
    setSystemPrompt1(DEFAULT_SYSTEM_PROMPTS.model1)
    setSystemPrompt2(DEFAULT_SYSTEM_PROMPTS.model2)
    toast.success('System prompts reset to defaults')
  }

  return (
    <div className="container py-6" style={{ 
      height: 'calc(100vh - 3rem)', 
      overflow: 'hidden', 
      display: 'flex', 
      flexDirection: 'column' 
    }}>
      <h2 className="text-2xl font-semibold mb-4">Chain Models</h2>
      
      <Tabs value={activeTab} onValueChange={setActiveTab} className="w-full flex-1 flex flex-col overflow-hidden">
        <TabsList className="mb-2">
          <TabsTrigger value="config">Configuration</TabsTrigger>
          <TabsTrigger value="results">Results</TabsTrigger>
        </TabsList>
        
        <TabsContent value="config" className="flex-1 overflow-auto">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
            <Card className="shadow-sm">
              <CardHeader className="p-3">
                <CardTitle className="text-lg">First Model</CardTitle>
              </CardHeader>
              <CardContent className="p-3 space-y-4">
                <ModelSelector
                  models={models}
                  selectedModel={selectedModel1}
                  onModelSelect={(model: ModelInfo) => setSelectedModel1(model)}
                />
                <div>
                  <h3 className="text-sm font-medium mb-2">System Prompt</h3>
                  <Textarea 
                    value={systemPrompt1}
                    onChange={(e) => setSystemPrompt1(e.target.value)}
                    className="min-h-[150px]"
                    placeholder="Enter system prompt for the first model..."
                  />
                </div>
              </CardContent>
            </Card>

            <Card className="shadow-sm">
              <CardHeader className="p-3">
                <CardTitle className="text-lg">Second Model</CardTitle>
              </CardHeader>
              <CardContent className="p-3 space-y-4">
                <ModelSelector
                  models={models}
                  selectedModel={selectedModel2}
                  onModelSelect={(model: ModelInfo) => setSelectedModel2(model)}
                />
                <div>
                  <h3 className="text-sm font-medium mb-2">System Prompt</h3>
                  <Textarea 
                    value={systemPrompt2}
                    onChange={(e) => setSystemPrompt2(e.target.value)}
                    className="min-h-[150px]"
                    placeholder="Enter system prompt for the second model..."
                  />
                </div>
              </CardContent>
            </Card>
          </div>
          
          <div className="flex justify-end mb-4">
            <Button variant="outline" onClick={resetSystemPrompts}>
              Reset System Prompts
            </Button>
          </div>
        </TabsContent>
        
        <TabsContent value="results" className="flex-1 flex flex-col overflow-hidden">
          <Card className="mb-2 shadow-sm flex-shrink-0">
            <CardHeader className="p-2">
              <CardTitle className="text-lg">User Prompt</CardTitle>
            </CardHeader>
            <CardContent className="p-2">
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
                  disabled={isLoading || !input.trim() || !selectedModel1 || !selectedModel2}
                >
                  <Send className="h-4 w-4" />
                  <span className="sr-only">Send</span>
                </Button>
              </form>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4 flex-1 min-h-0 overflow-hidden">
            <Card className="shadow-sm flex flex-col overflow-hidden">
              <CardHeader className="p-2 flex-shrink-0">
                <CardTitle className="text-lg">
                  Intermediate Result ({selectedModel1 ? selectedModel1.name : 'First Model'})
                </CardTitle>
              </CardHeader>
              <CardContent className="p-2 overflow-auto flex-grow">
                {isLoading && !intermediateResponse ? (
                  <div className="flex justify-center items-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                  </div>
                ) : intermediateResponse ? (
                  <div className="prose max-w-none">
                    <MarkdownRenderer content={intermediateResponse.content} />
                  </div>
                ) : (
                  <div className="text-center text-gray-500 h-32 flex items-center justify-center">
                    <p>Intermediate result will appear here</p>
                  </div>
                )}
              </CardContent>
            </Card>

            <Card className="shadow-sm flex flex-col overflow-hidden">
              <CardHeader className="p-2 flex-shrink-0">
                <CardTitle className="text-lg">
                  Final Result ({selectedModel2 ? selectedModel2.name : 'Second Model'})
                </CardTitle>
              </CardHeader>
              <CardContent className="p-2 overflow-auto flex-grow">
                {isLoading && !finalResponse ? (
                  <div className="flex justify-center items-center h-32">
                    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
                  </div>
                ) : finalResponse ? (
                  <div className="prose max-w-none">
                    <MarkdownRenderer content={finalResponse.content} />
                  </div>
                ) : (
                  <div className="text-center text-gray-500 h-32 flex items-center justify-center">
                    <p>Final result will appear here</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
          <div ref={messagesEndRef} />
        </TabsContent>
      </Tabs>
      <Toaster />
    </div>
  )
}
