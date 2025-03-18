import { ChatSession, Message } from '@/types';

interface RawSession {
  id: string;
  title: string;
  date: string;
  last_updated?: string;
  preview?: string;
  messages?: RawMessage[];
}

interface RawMessage {
  role: string;
  content: string;
  timestamp?: string;
}

const API_BASE_URL = 'http://localhost:8000/api/v1';

/**
 * API service for handling all backend communication
 */
export const apiService = {
  /**
   * Get all sessions from the backend
   */
  async getSessions(): Promise<ChatSession[]> {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch sessions: ${response.statusText}`);
      }
      
      const data = await response.json();
      if (data.sessions && Array.isArray(data.sessions)) {
        // Convert date strings to Date objects
        return data.sessions.map((session: RawSession) => ({
          ...session,
          date: new Date(session.date),
          last_updated: session.last_updated ? new Date(session.last_updated) : undefined
        }));
      }
      
      return [];
    } catch (error) {
      console.error('Error fetching sessions:', error);
      throw error;
    }
  },
  
  /**
   * Get a specific session with its messages
   */
  async getSession(sessionId: string, includeMessages = true): Promise<{ session: ChatSession, messages: Message[] }> {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}?include_messages=${includeMessages}`);
      
      if (!response.ok) {
        throw new Error(`Failed to fetch session: ${response.statusText}`);
      }
      
      const data = await response.json();
      if (data.session) {
        // Format session and messages
        const formattedSession = {
          ...data.session,
          date: new Date(data.session.date),
          last_updated: data.session.last_updated ? new Date(data.session.last_updated) : undefined
        };
        
        const formattedMessages = data.session.messages 
          ? data.session.messages.map((msg: RawMessage) => ({
              ...msg,
              timestamp: msg.timestamp ? new Date(msg.timestamp) : undefined
            }))
          : [];
          
        return {
          session: formattedSession,
          messages: formattedMessages
        };
      }
      
      throw new Error('Session not found');
    } catch (error) {
      console.error(`Error fetching session ${sessionId}:`, error);
      throw error;
    }
  },
  
  /**
   * Create a new session
   */
  async createSession(title = 'New Chat'): Promise<ChatSession> {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to create session: ${response.statusText}`);
      }
      
      const data = await response.json();
      if (data.session) {
        return {
          ...data.session,
          date: new Date(data.session.date),
          last_updated: data.session.last_updated ? new Date(data.session.last_updated) : undefined
        };
      }
      
      throw new Error('Failed to create session');
    } catch (error) {
      console.error('Error creating session:', error);
      throw error;
    }
  },
  
  /**
   * Update a session's title
   */
  async updateSession(sessionId: string, title: string): Promise<ChatSession> {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title }),
      });
      
      if (!response.ok) {
        throw new Error(`Failed to update session: ${response.statusText}`);
      }
      
      const data = await response.json();
      if (data.session) {
        return {
          ...data.session,
          date: new Date(data.session.date),
          last_updated: data.session.last_updated ? new Date(data.session.last_updated) : undefined
        };
      }
      
      throw new Error('Failed to update session');
    } catch (error) {
      console.error(`Error updating session ${sessionId}:`, error);
      throw error;
    }
  },
  
  /**
   * Delete a session
   */
  async deleteSession(sessionId: string): Promise<void> {
    try {
      const response = await fetch(`${API_BASE_URL}/sessions/${sessionId}`, {
        method: 'DELETE',
      });
      
      if (!response.ok) {
        throw new Error(`Failed to delete session: ${response.statusText}`);
      }
    } catch (error) {
      console.error(`Error deleting session ${sessionId}:`, error);
      throw error;
    }
  },
  
  /**
   * Send a chat message and get a response
   */
  async sendMessage(messages: Message[], model: string, systemPrompt: string | null, sessionId: string | null, stream = true): Promise<Response> {
    try {
      const requestBody = {
        messages: messages.map(msg => ({
          role: msg.role,
          content: msg.content
        })),
        model,
        stream,
        system_prompt: systemPrompt,
        session_id: sessionId
      };
      
      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });
      
      if (!response.ok) {
        throw new Error(`Chat request failed: ${response.statusText}`);
      }
      
      return response;
    } catch (error) {
      console.error('Error sending chat message:', error);
      throw error;
    }
  }
};
