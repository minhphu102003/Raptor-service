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
export interface ApiResponse<T> {
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