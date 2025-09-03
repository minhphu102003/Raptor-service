import { apiRequest } from './api'

// Types matching the backend models
export interface ChatSession {
  session_id: string
  dataset_id: string
  title: string
  user_id?: string
  assistant_id?: string
  assistant_config?: Record<string, unknown>
  status?: string
  message_count: number
  created_at: string
  updated_at: string
}

export interface CreateSessionRequest {
  dataset_id: string
  title?: string
  user_id?: string
  assistant_id?: string
  assistant_config?: Record<string, unknown>
}

// API Response wrapper
interface ApiResponse<T> {
  code: number
  data: T
  message?: string
}

export interface ContextPassage {
  id: string
  content: string
  score?: number
  metadata?: Record<string, unknown>
}

export interface ChatMessage {
  message_id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  context_passages?: ContextPassage[]
  model_used?: string
  processing_time_ms?: number
  created_at: string
}

export interface ChatSavedMessage {
  message_id: string
  session_id: string
  role: 'user' | 'assistant' | 'system'
  content: string
  context_passages?: ContextPassage[]
  model_used?: string
  processing_time_ms?: number
  created_at: string
}

export interface ChatMessageResponse {
  answer: string
  model: string
  top_k: number
  mode: string
  passages: ContextPassage[]
  session_id: string
  processing_time_ms: number
  user_message?: ChatSavedMessage
  assistant_message?: ChatSavedMessage
}

export interface ChatMessageRequest {
  query: string
  dataset_id: string
  session_id?: string
  top_k?: number
  expand_k?: number
  mode?: 'tree' | 'chunk'
  answer_model?: string
  temperature?: number
  max_tokens?: number
  stream?: boolean
}

// Enhanced chat message request
export interface EnhancedChatMessageRequest extends ChatMessageRequest {
  use_enhanced_context?: boolean
  max_context_messages?: number
  additional_context?: Record<string, unknown>
}

// Session context types
export interface SessionContext {
  session_id: string
  dataset_id: string
  assistant_id?: string
  message_count: number
  recent_messages: Array<{
    role: 'user' | 'assistant' | 'system'
    content: string
    timestamp?: string
  }>
  system_prompt?: string
  assistant_config?: Record<string, unknown>
}

export interface SessionContextSummary {
  session_id: string
  dataset_id: string
  assistant_id?: string
  message_count: number
  recent_message_count: number
  system_prompt?: string
  model_info?: string
  last_message_timestamp?: string
}

export interface ConversationSummary {
  session_id: string
  message_count: number
  recent_message_count: number
  topics_discussed: string[]
  model_used?: string
  conversation_length: 'short' | 'medium' | 'long'
}

export interface ClearContextResponse {
  message: string
}

// Chat Service
export const chatService = {
  // Create a new chat session
  createSession: async (data: CreateSessionRequest): Promise<ChatSession> => {
    const response = await apiRequest<ApiResponse<ChatSession>>('/datasets/chat/sessions', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    return response.data
  },

  // List chat sessions
  listSessions: async (datasetId?: string, assistantId?: string): Promise<ChatSession[]> => {
    const params = new URLSearchParams();
    if (datasetId) params.append('dataset_id', datasetId);
    if (assistantId) params.append('assistant_id', assistantId);
    
    const queryString = params.toString();
    const url = `/datasets/chat/sessions${queryString ? `?${queryString}` : ''}`;
    
    const response = await apiRequest<ApiResponse<ChatSession[]>>(url)
    return response.data
  },

  // Get a specific chat session
  getSession: async (sessionId: string): Promise<ChatSession> => {
    const response = await apiRequest<ApiResponse<ChatSession>>(`/datasets/chat/sessions/${sessionId}`)
    return response.data
  },

  // Update a chat session
  updateSession: async (
    sessionId: string,
    data: Partial<CreateSessionRequest>
  ): Promise<ChatSession> => {
    const response = await apiRequest<ApiResponse<ChatSession>>(`/datasets/chat/sessions/${sessionId}`, {
      method: 'PUT',
      body: JSON.stringify(data),
    })
    return response.data
  },

  // Delete a chat session
  deleteSession: async (sessionId: string): Promise<void> => {
    await apiRequest<ApiResponse<void>>(`/datasets/chat/sessions/${sessionId}`, {
      method: 'DELETE',
    })
  },

  // Get messages for a session
  getMessages: async (sessionId: string, limit = 50, offset = 0): Promise<ChatMessage[]> => {
    const response = await apiRequest<ApiResponse<ChatMessage[]>>(
      `/datasets/chat/sessions/${sessionId}/messages?limit=${limit}&offset=${offset}`
    )
    return response.data
  },

  // Send a chat message
  sendMessage: async (data: ChatMessageRequest): Promise<ChatMessageResponse> => {
    const response = await apiRequest<ApiResponse<ChatMessageResponse>>('/datasets/chat/chat', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    console.log('Raw chat response:', response)
    // The backend returns the data directly, not wrapped in a data field
    // If response has a data field, return it, otherwise return the response itself
    return response && typeof response === 'object' && 'data' in response 
      ? response.data 
      : response as ChatMessageResponse
  },

  // Send an enhanced chat message
  sendEnhancedMessage: async (data: EnhancedChatMessageRequest): Promise<ChatMessageResponse> => {
    const response = await apiRequest<ApiResponse<ChatMessageResponse>>('/datasets/chat/chat/enhanced', {
      method: 'POST',
      body: JSON.stringify(data),
    })
    console.log('Raw enhanced chat response:', response)
    // The backend returns the data directly, not wrapped in a data field
    // If response has a data field, return it, otherwise return the response itself
    return response && typeof response === 'object' && 'data' in response 
      ? response.data 
      : response as ChatMessageResponse
  },

  // Update session title
  updateSessionTitle: async (sessionId: string, title: string): Promise<ChatSession> => {
    const response = await apiRequest<ApiResponse<ChatSession>>(`/datasets/chat/sessions/${sessionId}`, {
      method: 'PUT',
      body: JSON.stringify({ title }),
    })
    return response.data
  },

  // Get session context
  getSessionContext: async (sessionId: string): Promise<SessionContext> => {
    const response = await apiRequest<ApiResponse<SessionContext>>(`/datasets/chat/sessions/${sessionId}/context`)
    return response.data
  },

  // Get session context summary
  getSessionContextSummary: async (sessionId: string): Promise<SessionContextSummary> => {
    const response = await apiRequest<ApiResponse<SessionContextSummary>>(`/datasets/chat/sessions/${sessionId}/context/summary`)
    return response.data
  },

  // Get conversation summary
  getConversationSummary: async (sessionId: string, maxMessages?: number): Promise<ConversationSummary> => {
    const params = new URLSearchParams();
    if (maxMessages) params.append('max_messages', maxMessages.toString());
    
    const queryString = params.toString();
    const url = `/datasets/chat/sessions/${sessionId}/context/conversation-summary${queryString ? `?${queryString}` : ''}`;
    
    const response = await apiRequest<ApiResponse<ConversationSummary>>(url)
    return response.data
  },

  // Clear session context
  clearSessionContext: async (sessionId: string): Promise<ClearContextResponse> => {
    const response = await apiRequest<ApiResponse<ClearContextResponse>>(`/datasets/chat/sessions/${sessionId}/context/clear`, {
      method: 'POST',
    })
    return response.data
  }
}