'use client'

import { useState, useEffect } from 'react'
import { Send } from 'lucide-react'

import { Input } from '@/components/ui/input'
import { ModelSelector } from '@/components/model-selector'
import { Separator } from '@/components/ui/separator'
import { MarkdownRenderer } from '@/components/markdown-renderer'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle, CardFooter } from '@/components/ui/card'
import { Message, Model } from '@/types'

export default function ComparePage() {
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [models, setModels] = useState<Model[]>([])
  const [selectedModelA, setSelectedModelA] = useState<Model | null>(null)
  const [selectedModelB, setSelectedModelB] = useState<Model | null>(null)
  const [responseA, setResponseA] = useState<Message | null>(null)
  const [responseB, setResponseB] = useState<Message | null>(null)

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

  return (
    <div className="container h-full flex flex-col overflow-hidden py-6">
      <h2 className="text-2xl font-semibold mb-6">Compare Model Responses</h2>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
        <Card className="shadow-sm">
          <CardHeader className="p-3">
            <CardTitle className="text-lg">Model A</CardTitle>
          </CardHeader>
          <CardContent className="p-3">
            <ModelSelector
              models={models}
              selectedModel={selectedModelA}
              onModelSelect={(model: Model) => setSelectedModelA(model)}
            />
          </CardContent>
        </Card>

        <Card className="shadow-sm">
          <CardHeader className="p-3">
            <CardTitle className="text-lg">Model B</CardTitle>
          </CardHeader>
          <CardContent className="p-3">
            <ModelSelector
              models={models}
              selectedModel={selectedModelB}
              onModelSelect={(model: Model) => setSelectedModelB(model)}
            />
          </CardContent>
        </Card>
      </div>

      <Card className="mb-6 shadow-sm">
        <CardHeader className="p-3">
          <CardTitle className="text-lg">Prompt</CardTitle>
        </CardHeader>
        <CardContent className="p-3">
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

      <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-6 overflow-y-auto pb-6">
        <Card className="shadow-sm h-full">
          <CardHeader className="p-3">
            <CardTitle className="text-lg">
              {selectedModelA ? selectedModelA.name : 'Model A'} Response
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3">
            {isLoading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
              </div>
            ) : responseA ? (
              <div className="prose max-w-none">
                <MarkdownRenderer content={responseA.content} />
              </div>
            ) : (
              <div className="text-center text-gray-500 h-64 flex items-center justify-center">
                <p>Response will appear here</p>
              </div>
            )}
          </CardContent>
        </Card>

        <Card className="shadow-sm h-full">
          <CardHeader className="p-3">
            <CardTitle className="text-lg">
              {selectedModelB ? selectedModelB.name : 'Model B'} Response
            </CardTitle>
          </CardHeader>
          <CardContent className="p-3">
            {isLoading ? (
              <div className="flex justify-center items-center h-64">
                <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-900"></div>
              </div>
            ) : responseB ? (
              <div className="prose max-w-none">
                <MarkdownRenderer content={responseB.content} />
              </div>
            ) : (
              <div className="text-center text-gray-500 h-64 flex items-center justify-center">
                <p>Response will appear here</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
