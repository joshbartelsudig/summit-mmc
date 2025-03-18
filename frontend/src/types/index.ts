// Common types used across the application

export type Message = {
  role: 'user' | 'assistant'
  content: string
  id?: string
  timestamp?: Date
}

export type ModelInfo = {
  id: string
  name: string
  provider: 'azure' | 'bedrock'
  inferenceProfile?: string
}

export type ChatSession = {
  id: string
  title: string
  date: Date
  preview: string
  message_count?: number
  model_id?: string
  last_updated?: Date
  messages?: Message[]
}
