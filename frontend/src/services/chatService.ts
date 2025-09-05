import { apiRequest, createApiUrl } from './api'
import type {
  ChatSession,
  CreateSessionRequest,
  ApiResponse,
  ContextPassage,
  ChatMessage,
  ChatMessageResponse,
  ChatMessageRequest,
  EnhancedChatMessageRequest,
  SessionContext,
  SessionContextSummary,
  ConversationSummary,
  ClearContextResponse
} from './chatTypes'

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
    // The backend returns the data directly, not wrapped in a data field
    // If response has a data field, return it, otherwise return the response itself
    return response && typeof response === 'object' && 'data' in response 
      ? response.data 
      : response as ChatMessageResponse
  },

  // Send a chat message with streaming support
  sendMessageStream: async (
    data: ChatMessageRequest,
    onChunk: (chunk: string) => void
  ): Promise<ChatMessageResponse> => {
    const url = createApiUrl('/datasets/chat/chat');
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ...data, stream: true }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let accumulatedContent = '';
    const finalResponseData: Partial<ChatMessageResponse> = {}; // To store final JSON data
    let done = false;

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;

      if (value) {
        const chunk = decoder.decode(value, { stream: true });
        
        // Check if this is the final JSON chunk (starts with \n and contains passages)
        if (chunk.startsWith('\n') && chunk.includes('"passages"')) {
          try {
            // Extract the JSON part after the newline
            const jsonPart = chunk.substring(1);
            const finalData = JSON.parse(jsonPart);
            // Don't send this to onChunk callback since it's metadata, not content
            accumulatedContent += finalData.answer || '';
            // We'll return this data at the end
            Object.assign(finalResponseData, finalData);
          } catch {
            // If parsing fails, treat it as regular content
            onChunk(chunk);
            accumulatedContent += chunk;
          }
        } else {
          // Regular content chunk
          onChunk(chunk);
          accumulatedContent += chunk;
        }
      }
    }

    // If we have final response data, use it; otherwise try to parse accumulated content
    if (Object.keys(finalResponseData).length > 0) {
      return finalResponseData as ChatMessageResponse;
    }

    // Try to parse the accumulated content as JSON
    try {
      const jsonResponse = JSON.parse(accumulatedContent);
      return jsonResponse;
    } catch {
      // Try to extract specific fields from the raw content
      let extractedAnswer = accumulatedContent;
      let extractedPassages: ContextPassage[] = [];
      
      try {
        // Try to find answer in the raw content
        const answerMatch = accumulatedContent.match(/"answer":"([^"]*)"/) || 
                           accumulatedContent.match(/"answer":(".*?")[,}]/s);
        if (answerMatch) {
          // Handle escaped quotes in the answer
          extractedAnswer = JSON.parse(answerMatch[1]);
        }
        
        // Try to find passages in the raw content
        const passagesMatch = accumulatedContent.match(/"passages":(\[[\s\S]*?\])(?=,|})/);
        if (passagesMatch) {
          try {
            extractedPassages = JSON.parse(passagesMatch[1]);
          } catch {
            // Ignore parsing errors
          }
        }
      } catch {
        // Ignore extraction errors
      }
      
      // Return a response with extracted fields if possible
      return {
        answer: extractedAnswer,
        model: data.answer_model || 'default',
        top_k: data.top_k || 5,
        mode: data.mode || 'tree',
        passages: extractedPassages,
        session_id: data.session_id || '',
        processing_time_ms: 0,
      } as ChatMessageResponse;
    }
  },

  // Send an enhanced chat message with streaming support
  sendEnhancedMessageStream: async (
    data: EnhancedChatMessageRequest,
    onChunk: (chunk: string) => void
  ): Promise<ChatMessageResponse> => {
    const url = createApiUrl('/datasets/chat/chat/enhanced');
    
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ ...data, stream: true }),
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let accumulatedContent = '';
    const finalResponseData: Partial<ChatMessageResponse> = {}; // To store final JSON data
    let done = false;

    while (!done) {
      const { value, done: readerDone } = await reader.read();
      done = readerDone;

      if (value) {
        const chunk = decoder.decode(value, { stream: true });
        
        // Check if this is the final JSON chunk (starts with \n and contains passages)
        if (chunk.startsWith('\n') && chunk.includes('"passages"')) {
          try {
            // Extract the JSON part after the newline
            const jsonPart = chunk.substring(1);
            const finalData = JSON.parse(jsonPart);
            // Don't send this to onChunk callback since it's metadata, not content
            accumulatedContent += finalData.answer || '';
            // We'll return this data at the end
            Object.assign(finalResponseData, finalData);
          } catch {
            // If parsing fails, treat it as regular content
            onChunk(chunk);
            accumulatedContent += chunk;
          }
        } else {
          // Regular content chunk
          onChunk(chunk);
          accumulatedContent += chunk;
        }
      }
    }

    // If we have final response data, use it; otherwise try to parse accumulated content
    if (Object.keys(finalResponseData).length > 0) {
      return finalResponseData as ChatMessageResponse;
    }

    // Try to parse the accumulated content as JSON
    try {
      const jsonResponse = JSON.parse(accumulatedContent);
      return jsonResponse;
    } catch {
      // Try to extract specific fields from the raw content
      let extractedAnswer = accumulatedContent;
      let extractedPassages: ContextPassage[] = [];
      
      try {
        // Try to find answer in the raw content
        const answerMatch = accumulatedContent.match(/"answer":"([^"]*)"/) || 
                           accumulatedContent.match(/"answer":(".*?")[,}]/s);
        if (answerMatch) {
          // Handle escaped quotes in the answer
          extractedAnswer = JSON.parse(answerMatch[1]);
        }
        
        // Try to find passages in the raw content
        const passagesMatch = accumulatedContent.match(/"passages":(\[[\s\S]*?\])(?=,|})/);
        if (passagesMatch) {
          try {
            extractedPassages = JSON.parse(passagesMatch[1]);
          } catch {
            // Ignore parsing errors
          }
        }
      } catch {
        // Ignore extraction errors
      }
      
      // Return a response with extracted fields if possible
      return {
        answer: extractedAnswer,
        model: data.answer_model || 'default',
        top_k: data.top_k || 5,
        mode: data.mode || 'tree',
        passages: extractedPassages,
        session_id: data.session_id || '',
        processing_time_ms: 0,
      } as ChatMessageResponse;
    }
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