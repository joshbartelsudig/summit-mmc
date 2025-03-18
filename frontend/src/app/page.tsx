"use client"

import { useState, useRef, useEffect } from 'react'
import { Send } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardFooter, CardHeader, CardDescription } from '@/components/ui/card'
import { Textarea } from '@/components/ui/textarea'
import { ChatHistory } from '@/components/chat-history'
import { ModelSelector } from '@/components/model-selector'
import { ChatMessage } from '@/components/chat-message'
import { Message, ChatSession, ModelInfo } from '@/types'
import { v4 as uuidv4 } from 'uuid'
import { toast } from 'sonner'
import { apiService } from '@/services/api'

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
  const [systemPrompt, setSystemPrompt] = useState<string | null>(null)
  const [forceRefresh, setForceRefresh] = useState(0); // Counter to force re-renders
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Initialize with a default session if none exists
  useEffect(() => {
    const initializeSessions = async () => {
      try {
        // Try to fetch sessions from backend
        const sessions = await apiService.getSessions();
        
        // Sort sessions by date (newest first)
        const sortedSessions = sessions.sort((a, b) => {
          const dateA = a.last_updated || a.date;
          const dateB = b.last_updated || b.date;
          return dateB.getTime() - dateA.getTime();
        });
        
        setSessions(sortedSessions);
        
        // Select the first session if there is one
        if (sortedSessions.length > 0) {
          const firstSession = sortedSessions[0];
          setSelectedSessionId(firstSession.id);
          setCurrentSession(firstSession);
          
          // Try to load messages for this session
          try {
            const { messages: sessionMessages } = await apiService.getSession(firstSession.id);
            if (sessionMessages && sessionMessages.length > 0) {
              setMessages(sessionMessages);
            }
          } catch (error) {
            console.error('Error loading session messages:', error);
          }
        } else {
          // Create a new session if none exist
          handleNewChat();
        }
      } catch (error) {
        console.error('Error initializing sessions:', error);
        
        // Fallback to local session creation
        if (sessions.length === 0) {
          handleNewChat();
        }
      }
    };
    
    initializeSessions();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // We intentionally want this to run only once on mount

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
  }, [selectedModel]); // Include selectedModel as dependency

  // Update session title and preview based on first message
  useEffect(() => {
    if (messages.length === 1 && messages[0].role === 'user' && currentSession) {
      const userMessage = messages[0];
      const sessionId = currentSession.id;
      const newTitle = userMessage.content.slice(0, 30) + (userMessage.content.length > 30 ? '...' : '');

      // Update session title in the backend
      apiService.updateSession(sessionId, newTitle)
        .then(() => {
          // Update sessions list with the updated session
          setSessions(prev =>
            prev.map(s =>
              s.id === sessionId
                ? { ...s, title: newTitle, preview: userMessage.content }
                : s
            )
          );
          
          // Update current session
          setCurrentSession(prev =>
            prev && prev.id === sessionId
              ? { ...prev, title: newTitle, preview: userMessage.content }
              : prev
          );
        })
        .catch(error => {
          console.error('Error updating session title:', error);
          // Still update the local state even if backend fails
          setSessions(prev =>
            prev.map(s =>
              s.id === sessionId
                ? { ...s, title: newTitle, preview: userMessage.content }
                : s
            )
          );
          
          setCurrentSession(prev =>
            prev && prev.id === sessionId
              ? { ...prev, title: newTitle, preview: userMessage.content }
              : prev
          );
        });
    }
  }, [messages, currentSession]); // Added currentSession as dependency

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages])

  // Handle creating a new chat
  const handleNewChat = async () => {
    // Check if we should allow creating a new chat
    // If there are no messages in the current chat, don't create a new one
    if (messages.length === 0 && currentSession) {
      // Just reset the current chat state
      setInput('');
      setIsLoading(false);
      setSystemPrompt(null);
      return;
    }
    
    // Reset chat window state
    setInput('');
    setMessages([]);
    setIsLoading(false);
    setSystemPrompt(null);
    
    try {
      // Create a new session in the backend
      const newSession = await apiService.createSession('New Chat');
      
      // Update state with the new session
      setSessions(prev => {
        // Add the new session
        const updated = [newSession, ...prev];
        
        // Sort by date (newest first)
        return updated.sort((a, b) => {
          const dateA = a.last_updated || a.date;
          const dateB = b.last_updated || b.date;
          return dateB.getTime() - dateA.getTime();
        });
      });
      
      // Select the new session
      setSelectedSessionId(newSession.id);
      setCurrentSession(newSession);
    } catch (error) {
      console.error('Error creating new session:', error);
      toast.error('Failed to create new chat session');
      
      // Fallback to local session creation
      const newSessionId = uuidv4();
      const newSession: ChatSession = {
        id: newSessionId,
        title: 'New Chat',
        date: new Date(),
        preview: ''
      };

      setSessions(prev => [newSession, ...prev]);
      setSelectedSessionId(newSessionId);
      setCurrentSession(newSession);
    }
  };

  // Handle selecting a session
  const handleSelectSession = async (sessionId: string) => {
    // Reset input and loading state
    setInput('');
    setIsLoading(false);
    setSystemPrompt(null);
    setMessages([]); // Reset messages initially
    
    setSelectedSessionId(sessionId);
    const session = sessions.find(s => s.id === sessionId);
    
    if (session) {
      setCurrentSession(session);
      
      try {
        // Load messages for this session from the backend
        const { messages: sessionMessages } = await apiService.getSession(sessionId);
        if (sessionMessages && sessionMessages.length > 0) {
          setMessages(sessionMessages);
        }
      } catch (error) {
        console.error('Error loading session messages:', error);
        toast.error('Failed to load chat messages');
      }
    }
  };

  // Handle deleting a session
  const handleDeleteSession = async (sessionId: string) => {
    try {
      // Delete from backend
      await apiService.deleteSession(sessionId);
      
      // Update local state
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      
      // If the deleted session was selected, select another one or create a new one
      if (selectedSessionId === sessionId) {
        // Reset state
        setInput('');
        setIsLoading(false);
        setSystemPrompt(null);
        setMessages([]);
        
        if (sessions.length > 1) {
          const newSelectedSession = sessions.find(s => s.id !== sessionId);
          if (newSelectedSession) {
            handleSelectSession(newSelectedSession.id);
          } else {
            handleNewChat();
          }
        } else {
          handleNewChat();
        }
      }
    } catch (error) {
      console.error('Error deleting session:', error);
      toast.error('Failed to delete chat session');
      
      // Still update local state even if backend fails
      setSessions(prev => prev.filter(s => s.id !== sessionId));
      
      if (selectedSessionId === sessionId) {
        if (sessions.length > 1) {
          const newSelectedSession = sessions.find(s => s.id !== sessionId);
          if (newSelectedSession) {
            handleSelectSession(newSelectedSession.id);
          } else {
            handleNewChat();
          }
        } else {
          handleNewChat();
        }
      }
    }
  };

  // Handle sending a message
  const handleSendMessage = async () => {
    if (!input.trim()) return;

    const userMessage: Message = {
      role: 'user',
      content: input.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');

    try {
      setIsLoading(true);

      // Send the message to the backend
      const response = await apiService.sendMessage(
        [...messages, userMessage],
        selectedModel.id,
        systemPrompt,
        selectedSessionId,
        streamingEnabled
      );

      if (streamingEnabled && response.body) {
        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let partialData = '';
        const assistantMessage: Message = {
          role: 'assistant',
          content: '',
          timestamp: new Date()
        };

        // Add an empty assistant message that we'll update as we stream
        setMessages(prev => [...prev, assistantMessage]);

        const processStream = async () => {
          try {
            while (true) {
              const { done, value } = await reader.read();
              if (done) break;

              const chunk = decoder.decode(value, { stream: true });
              partialData += chunk;

              // Process all complete JSON objects in the chunk
              let lastJsonEnd = 0;
              while (true) {
                const jsonStart = partialData.indexOf('{', lastJsonEnd);
                if (jsonStart === -1) break;

                try {
                  const jsonEnd = partialData.indexOf('}', jsonStart) + 1;
                  if (jsonEnd === 0) break; // No complete JSON object yet

                  const jsonStr = partialData.substring(jsonStart, jsonEnd);
                  const data = JSON.parse(jsonStr);

                  if (data.content) {
                    // Check if this is the [DONE] marker
                    if (data.content === '[DONE]') {
                      console.log('Stream completed with DONE marker');
                      setIsLoading(false);
                      
                      // Force a refresh after a small delay to ensure Mermaid diagrams render
                      setTimeout(() => {
                        setForceRefresh(prev => prev + 1);
                      }, 300);
                      
                      break;
                    }
                    
                    // Update the assistant message with the new content
                    assistantMessage.content += data.content;
                    setMessages(prev => {
                      const updated = [...prev];
                      updated[updated.length - 1] = { ...assistantMessage };
                      return updated;
                    });
                  }

                  lastJsonEnd = jsonEnd;
                } catch {
                  break; // Incomplete JSON, wait for more data
                }
              }

              // Remove processed JSON objects from partialData
              if (lastJsonEnd > 0) {
                partialData = partialData.substring(lastJsonEnd);
              }
            }
          } catch {
            // Ignore error
          }
        };

        await processStream();
      } else {
        const data = await response.json();
        setMessages(prev => {
          const lastMessage = prev[prev.length - 1];
          if (lastMessage.role === 'assistant') {
            return prev; // Don't add another assistant message if one exists
          }
          return [...prev, { role: 'assistant', content: data.response, timestamp: new Date() }];
        });
      }
    } catch (error) {
      console.error('Error:', error);
      toast.error('Failed to get a response. Please try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-1 overflow-hidden">
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
          <CardHeader className="border-b px-4 py-2 flex flex-row items-center justify-between">
            <div className="flex items-center gap-4">
              <CardDescription className="text-xs text-muted-foreground">
                {selectedModel
                  ? `Using ${selectedModel.id.includes('anthropic') || selectedModel.id.includes('amazon') ? 'Amazon Bedrock' : 'Azure OpenAI'}`
                  : 'Select a model to start chatting'
                }
              </CardDescription>
              <div className="flex items-center space-x-2">
                <input
                  id="streaming"
                  type="checkbox"
                  checked={streamingEnabled}
                  onChange={(e) => setStreamingEnabled(e.target.checked)}
                  className="h-4 w-4"
                />
                <label htmlFor="streaming" className="text-xs cursor-pointer">Enable streaming</label>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <ModelSelector
                models={models}
                selectedModel={selectedModel}
                onModelSelect={setSelectedModel}
                onSystemPromptChange={setSystemPrompt}
              />
            </div>
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
                  <ChatMessage key={`${index}-${forceRefresh}`} message={message} />
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </CardContent>
          <CardFooter className="border-t p-4 bg-background chat-footer">
            <form onSubmit={(event) => { event.preventDefault(); handleSendMessage(); }} className="flex w-full items-center space-x-2">
              <Textarea
                value={input}
                onChange={(e) => setInput(e.target.value)}
                placeholder="Type your message..."
                className="min-h-10 max-h-32 resize-none flex-1"
                rows={1}
                disabled={isLoading || !selectedModel}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSendMessage();
                  }
                }}
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
