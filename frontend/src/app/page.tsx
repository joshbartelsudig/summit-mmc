"use client"

import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardDescription } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { ChatMessage } from '@/components/chat-message'
import { ModelSelector } from '@/components/model-selector'
import { ChatHistory } from '@/components/chat-history'
import { v4 as uuidv4 } from 'uuid'
import { Message, ModelInfo, ChatSession } from '@/types'
import { Checkbox } from '@/components/ui/checkbox'
import { Label } from '@/components/ui/label'
import { Toaster } from '@/components/ui/sonner'
import { toast } from 'sonner'

// Function to handle streaming response
async function handleStreamingResponse(response: Response, onChunk: (chunk: string) => void) {
  if (!response.body) return;

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = '';

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      // Decode the chunk and add to buffer
      buffer += decoder.decode(value, { stream: true });

      // Process complete SSE messages
      const lines = buffer.split('\n');
      buffer = '';  // Clear buffer as we'll add back incomplete lines

      for (let i = 0; i < lines.length; i++) {
        const line = lines[i].trim();

        // Keep incomplete lines in buffer
        if (i === lines.length - 1 && line) {
          buffer = line;
          continue;
        }

        // Skip empty lines
        if (!line) continue;

        // Parse SSE data
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));

            // Check for end of stream
            if (data.content === '[DONE]') {
              return;
            }

            // Process content
            if (data.content) {
              onChunk(data.content);
            }
          } catch (error) {
            console.error('Error parsing SSE data:', error);
          }
        }
      }
    }

    // Process any remaining content in the buffer
    if (buffer) {
      const line = buffer.trim();
      if (line.startsWith('data: ')) {
        try {
          const data = JSON.parse(line.slice(6));
          if (data.content && data.content !== '[DONE]') {
            onChunk(data.content);
          }
        } catch (error) {
          console.error('Error parsing final SSE data:', error);
        }
      }
    }
  } catch (error) {
    console.error('Error reading stream:', error);
    throw error;
  }
}

export default function Home() {
  const [input, setInput] = useState('');
  const [messages, setMessages] = useState<Message[]>([]);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState<ModelInfo | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [streamingEnabled, setStreamingEnabled] = useState(true);
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null)
  const [currentSession, setCurrentSession] = useState<ChatSession | null>(null)
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Fetch models on component mount
  useEffect(() => {
    const fetchModels = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/v1/models')
        if (!response.ok) {
          throw new Error('Failed to fetch models')
        }
        const data = await response.json()
        setModels(data.models || [])

        // Set default model if none selected and models are available
        if (!selectedModel && data.models && data.models.length > 0) {
          setSelectedModel(data.models[0])
        }
      } catch (error) {
        console.error('Error fetching models:', error)
        toast.error('Failed to fetch available models')
      }
    }

    fetchModels()
  }, [selectedModel]) // Added selectedModel as dependency

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Initialize with a default session if none exists
  useEffect(() => {
    if (sessions.length === 0) {
      const newSessionId = uuidv4()
      const newSession: ChatSession = {
        id: newSessionId,
        title: 'New Chat',
        date: new Date(),
        preview: ''
      }

      setSessions([newSession])
      setSelectedSessionId(newSessionId)
      setCurrentSession(newSession)
    }
  }, [sessions.length]) // Added sessions.length as dependency

  // Update session title and preview based on first message
  useEffect(() => {
    if (messages.length > 0 && currentSession) {
      const userMessage = messages.find(m => m.role === 'user')
      if (userMessage) {
        // Store current session ID to avoid stale closures
        const sessionId = currentSession.id
        const newTitle = userMessage.content.slice(0, 30) + (userMessage.content.length > 30 ? '...' : '')

        setSessions(prev =>
          prev.map(s =>
            s.id === sessionId
              ? { ...s, title: newTitle, preview: userMessage.content }
              : s
          )
        )

        // Only update currentSession if the title or preview has changed
        if (currentSession.title !== newTitle || currentSession.preview !== userMessage.content) {
          setCurrentSession(prev =>
            prev && prev.id === sessionId
              ? { ...prev, title: newTitle, preview: userMessage.content }
              : prev
          )
        }
      }
    }
  }, [messages, currentSession]) // Added currentSession as dependency

  // Handle creating a new chat
  const handleNewChat = () => {
    const newSessionId = uuidv4()
    const newSession: ChatSession = {
      id: newSessionId,
      title: 'New Chat',
      date: new Date(),
      preview: ''
    }

    setSessions(prev => [newSession, ...prev])
    setSelectedSessionId(newSessionId)
    setCurrentSession(newSession)
    setMessages([])
  }

  // Handle selecting a session
  const handleSelectSession = (sessionId: string) => {
    setSelectedSessionId(sessionId)
    const session = sessions.find(s => s.id === sessionId)
    if (session) {
      setCurrentSession(session)
      // Here you would load the messages for this session from your backend
      // For now, we'll just clear the messages
      setMessages([])
    }
  }

  // Handle deleting a session
  const handleDeleteSession = (sessionId: string) => {
    setSessions(prev => prev.filter(s => s.id !== sessionId))
    if (selectedSessionId === sessionId) {
      if (sessions.length > 1) {
        const newSelectedSession = sessions.find(s => s.id !== sessionId)
        if (newSelectedSession) {
          setSelectedSessionId(newSelectedSession.id)
          setCurrentSession(newSelectedSession)
        }
      } else {
        handleNewChat()
      }
    }
  }

  // Handle form submission
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || !selectedModel) return;

    const userMessage: Message = {
      id: uuidv4(),
      role: 'user',
      content: input,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      setIsLoading(true);

      const endpoint = streamingEnabled ?
        'http://localhost:8000/api/v1/chat/stream' :
        'http://localhost:8000/api/v1/chat';

      const response = await fetch(endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Accept': streamingEnabled ? 'text/event-stream' : 'application/json',
        },
        body: JSON.stringify({
          messages: [...messages, userMessage].map(m => ({
            role: m.role,
            content: m.content
          })),
          model: selectedModel.id,
          stream: streamingEnabled
        })
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => null);
        throw new Error(
          errorData?.detail ||
          `Server error: ${response.status} ${response.statusText}`
        );
      }

      const assistantMessage: Message = {
        id: uuidv4(),
        role: 'assistant',
        content: '',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);

      if (streamingEnabled) {
        let content = '';

        await handleStreamingResponse(response, (chunk) => {
          // Accumulate the content
          content += chunk;

          setMessages(prev => {
            const lastMessage = prev[prev.length - 1];
            if (lastMessage.role === 'assistant') {
              return [
                ...prev.slice(0, -1),
                { ...lastMessage, content }
              ];
            }
            return prev;
          });
        });
      } else {
        const data = await response.json();
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage.role === 'assistant') {
            return [
              ...prev.slice(0, -1),
              { ...lastMessage, content: data.choices[0].message.content }
            ];
          }
          return prev;
        });
      }
    } catch (error) {
      console.error('Error:', error);
      const errorMessage = error instanceof Error ? error.message : 'Failed to get response';
      toast.error(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  return (


      <div className="flex flex-1 overflow-hidden">
        <Toaster />
        <div className="w-64 hidden md:block">
        <ChatHistory
          sessions={sessions}
          onSelectSession={handleSelectSession}
          onDeleteSession={handleDeleteSession}
          onNewChat={handleNewChat}
          selectedSessionId={selectedSessionId}
        />
      </div>

      {/* Main Chat Area */}
      <div className="flex-1">
        <Card className="h-full flex flex-col rounded-none border-0 md:border-l">
          <CardHeader className="border-b px-4 py-2 flex flex-row items-center justify-between chat-header">
            <div className="flex items-center gap-4">
              <CardDescription className="text-xs text-muted-foreground">
                {
                  selectedModel ?
                  `Using ${selectedModel.id.includes('anthropic') || selectedModel.id.includes('amazon') ? 'Amazon Bedrock' : 'Azure OpenAI'}` :
                  'Select a model to start chatting'
                }
              </CardDescription>
              <div className="flex items-center space-x-2">
                <Checkbox
                  id="streaming"
                  checked={streamingEnabled}
                  onCheckedChange={(checked) => setStreamingEnabled(checked === true)}
                  className="h-4 w-4"
                />
                <Label htmlFor="streaming" className="text-xs cursor-pointer">Enable streaming</Label>
              </div>
            </div>
            <ModelSelector
              selectedModel={selectedModel}
              onModelSelect={setSelectedModel}
              models={models}
            />
          </CardHeader>
          <CardContent className="flex-1 overflow-y-auto p-4 space-y-4">
              {messages.length === 0 ? (
                <div className="flex h-full items-center justify-center text-center">
                  <div className="space-y-2">
                    <h3 className="text-lg font-medium">Welcome to AI Chat</h3>
                    <p className="text-sm text-muted-foreground">
                      Start a conversation with Azure OpenAI or Amazon Bedrock models.
                    </p>
                  </div>
                </div>
              ) : (
                <div className="space-y-4 pb-4">
                  {messages.map((message, index) => (
                    <ChatMessage key={index} message={message} />
                  ))}
                  <div ref={messagesEndRef} />
                </div>
              )}
          </CardContent>
          <CardFooter className="border-t p-4 bg-background chat-footer">
            <form onSubmit={handleSubmit} className="flex w-full items-center space-x-2">
              <Input
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                disabled={isLoading || !selectedModel}
                className="flex-1"
              />
              <Button type="submit" disabled={isLoading || !selectedModel || !input.trim()}>
                <Send className="h-4 w-4 mr-2" />
                {isLoading ? 'Sending...' : 'Send'}
              </Button>
            </form>
          </CardFooter>
        </Card>
        </div>
      </div>

  )
}
