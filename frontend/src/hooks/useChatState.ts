import { useState, useCallback, useEffect } from 'react'
import { UuidUtils } from '../utils'
import { chatService, type CreateSessionRequest, type ChatMessageRequest, type EnhancedChatMessageRequest } from '../services/chatService'

// Type definitions
export interface Assistant {
  id: string
  user_id?: string
  name: string
  description?: string
  knowledgeBases: string[]
  modelSettings: {
    model: string
    temperature: number
    topP: number
    presencePenalty: number
    frequencyPenalty: number
  }
  systemPrompt?: string
  status: string
  meta?: Record<string, unknown>
  createdAt: string
  updatedAt: string
  datasets?: Array<{
    id: string
    name: string
    description?: string
    doc_count: number
    created_at: string
  }>
}

export interface ChatSession {
  id: string
  name: string
  assistantId: string
  createdAt: Date
  messageCount: number
  lastMessage?: string
}

export interface Message {
  id: string
  sessionId: string
  type: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
  contextPassages?: Array<{
    id: string
    content: string
    score?: number
    metadata?: Record<string, unknown>
  }>
}

export interface UploadedFile {
  id: string
  name: string
  type: string
  size: number
  uploadedAt: Date
  status: 'uploading' | 'completed' | 'failed'
}

export const useChatState = () => {
  const [selectedAssistant, setSelectedAssistant] = useState<Assistant | null>(null)
  const [selectedSession, setSelectedSession] = useState<ChatSession | null>(null)
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])
  const [loadingSessions, setLoadingSessions] = useState(false)
  const [loadingMessages, setLoadingMessages] = useState(false)

  // Load sessions for the selected assistant
  useEffect(() => {
    const loadSessions = async () => {
      if (selectedAssistant) {
        setLoadingSessions(true)
        try {
          // Load sessions from backend for this assistant and the first knowledge base (dataset)
          const apiSessions = await chatService.listSessions(
            selectedAssistant.knowledgeBases[0], 
            selectedAssistant.id
          )
          const convertedSessions: ChatSession[] = apiSessions.map(session => ({
            id: session.session_id,
            name: session.title,
            assistantId: session.assistant_id || selectedAssistant.id,
            createdAt: new Date(session.created_at),
            messageCount: session.message_count
          }))
          setSessions(convertedSessions)
          
          // If there's a selected session and it's not in the new list, clear it
          if (selectedSession && !convertedSessions.some(s => s.id === selectedSession.id)) {
            setSelectedSession(null)
            setMessages([])
          }
        } catch (error) {
          console.error('Failed to load sessions:', error)
          setSessions([])
        } finally {
          setLoadingSessions(false)
        }
      } else {
        setSessions([])
        setSelectedSession(null)
        setMessages([])
        setLoadingSessions(false)
      }
    }

    loadSessions()
  }, [selectedAssistant, selectedSession])

  // Load messages when session changes
  useEffect(() => {
    const loadMessages = async () => {
      if (selectedSession) {
        setLoadingMessages(true)
        try {
          // Load messages from backend for this session
          const apiMessages = await chatService.getMessages(selectedSession.id)
          const convertedMessages: Message[] = apiMessages.map(msg => ({
            id: msg.message_id,
            sessionId: msg.session_id,
            type: msg.role,
            content: msg.content,
            timestamp: new Date(msg.created_at),
            contextPassages: msg.context_passages
          }))
          setMessages(convertedMessages)
        } catch (error) {
          console.error('Failed to load messages:', error)
          setMessages([])
        } finally {
          setLoadingMessages(false)
        }
      } else {
        setMessages([])
      }
    }

    loadMessages()
  }, [selectedSession])

  // Assistant management
  const selectAssistant = useCallback((assistant: Assistant | null) => {
    setSelectedAssistant(assistant)
    // Don't automatically create sessions - let user do it explicitly
  }, [])

  // Session management
  const createNewSession = useCallback(async (assistantId: string, sessionName?: string) => {
    if (!selectedAssistant) return null

    try {
      // Create session in backend
      const requestData: CreateSessionRequest = {
        dataset_id: selectedAssistant.knowledgeBases[0],
        title: sessionName || `New Chat ${sessions.length + 1}`,
        assistant_id: assistantId
      }
      
      const apiSession = await chatService.createSession(requestData)
      
      const newSession: ChatSession = {
        id: apiSession.session_id,
        name: apiSession.title,
        assistantId: apiSession.assistant_id || assistantId,
        createdAt: new Date(apiSession.created_at),
        messageCount: apiSession.message_count
      }

      setSessions(prev => [...prev, newSession])
      setSelectedSession(newSession)
      setMessages([])
      return newSession
    } catch (error) {
      console.error('Failed to create session:', error)
      return null
    }
  }, [selectedAssistant, sessions.length])

  const selectSession = useCallback((session: ChatSession | null) => {
    setSelectedSession(session)
    // Messages will be loaded automatically by the useEffect hook
  }, [])

  // Message management
  const addMessage = useCallback((message: Omit<Message, 'id'>) => {
    const newMessage: Message = {
      ...message,
      id: UuidUtils.generateMessageId()
    }

    setMessages(prev => [...prev, newMessage])

    // Update session with last message and count
    if (selectedSession) {
      // If this is the first user message, update the session title
      const userMessages = messages.filter(msg => msg.type === 'user')
      if (userMessages.length === 0 && message.type === 'user') {
        // This is the first user message, update session title
        const truncatedTitle = message.content.length > 50 
          ? message.content.substring(0, 47) + '...' 
          : message.content

        // Update in backend
        chatService.updateSessionTitle(selectedSession.id, truncatedTitle).catch(err => {
          console.error('Failed to update session title:', err)
        })

        // Update in frontend
        setSessions(prev => prev.map(session =>
          session.id === selectedSession.id
            ? {
                ...session,
                name: truncatedTitle,
                lastMessage: message.content,
                messageCount: session.messageCount + 1
              }
            : session
        ))
      } else {
        // Not the first user message, just update message count and last message
        setSessions(prev => prev.map(session =>
          session.id === selectedSession.id
            ? {
                ...session,
                lastMessage: message.type === 'user' ? message.content : session.lastMessage,
                messageCount: session.messageCount + 1
              }
            : session
        ))
      }
    }

    return newMessage
  }, [selectedSession, messages])

  // Send message to assistant
  const sendMessageToAssistant = useCallback(async (content: string, sessionId: string, datasetId: string) => {
    try {
      // Create message request
      const messageRequest: ChatMessageRequest = {
        query: content,
        dataset_id: datasetId,
        session_id: sessionId,
        // Use assistant model settings if available
        answer_model: selectedAssistant?.modelSettings?.model || 'DeepSeek-V3',
        temperature: selectedAssistant?.modelSettings?.temperature || 0.7,
        max_tokens: 4000,
        top_k: 5,
        expand_k: 5,
        mode: 'tree',
        stream: false
      }

      // Send message to backend
      const response = await chatService.sendMessage(messageRequest)
      console.log('Processed chat response:', response)
      
      // Handle the response based on its format
      let userMessage: Message;
      let assistantMessage: Message;
      
      // Check if response has the expected structure with user_message and assistant_message
      if (response && typeof response === 'object' && 'user_message' in response && 'assistant_message' in response && 
          response.user_message && response.assistant_message) {
        // New format with saved messages
        userMessage = {
          id: response.user_message.message_id,
          sessionId: response.user_message.session_id,
          type: 'user' as const,
          content: response.user_message.content,
          timestamp: new Date(response.user_message.created_at)
        };
        
        assistantMessage = {
          id: response.assistant_message.message_id,
          sessionId: response.assistant_message.session_id,
          type: 'assistant' as const,
          content: response.assistant_message.content,
          timestamp: new Date(response.assistant_message.created_at),
          contextPassages: response.assistant_message.context_passages
        };
      } else {
        // Handle direct response format (answer, passages, etc.)
        // Fallback to old format (generate IDs client-side)
        userMessage = {
          id: UuidUtils.generateMessageId(),
          sessionId: sessionId,
          type: 'user',
          content: content,
          timestamp: new Date()
        };
        
        assistantMessage = {
          id: UuidUtils.generateMessageId(),
          sessionId: sessionId,
          type: 'assistant',
          content: response && typeof response === 'object' && 'answer' in response 
            ? response.answer 
            : 'Sorry, I couldn\'t process that request.',
          timestamp: new Date(),
          contextPassages: response && typeof response === 'object' && 'passages' in response 
            ? response.passages 
            : []
        };
      }
      
      setMessages(prev => [...prev, userMessage, assistantMessage])
      
      // Update session message count
      if (selectedSession) {
        setSessions(prev => prev.map(session =>
          session.id === selectedSession.id
            ? {
                ...session,
                messageCount: session.messageCount + 2,
                lastMessage: content
              }
            : session
        ))
      }
      
      return { userMessage, assistantMessage }
    } catch (error) {
      console.error('Failed to send message:', error)
      throw error
    }
  }, [selectedAssistant, selectedSession])

  // Send enhanced message to assistant
  const sendEnhancedMessageToAssistant = useCallback(async (content: string, sessionId: string, datasetId: string, additionalContext?: Record<string, unknown>) => {
    try {
      // Create enhanced message request
      const messageRequest: EnhancedChatMessageRequest = {
        query: content,
        dataset_id: datasetId,
        session_id: sessionId,
        use_enhanced_context: true,
        max_context_messages: 6,
        additional_context: additionalContext,
        // Use assistant model settings if available
        answer_model: selectedAssistant?.modelSettings?.model || 'DeepSeek-V3',
        temperature: selectedAssistant?.modelSettings?.temperature || 0.7,
        max_tokens: 4000,
        top_k: 5,
        expand_k: 5,
        mode: 'tree',
        stream: false
      }

      // Send enhanced message to backend
      const response = await chatService.sendEnhancedMessage(messageRequest)
      console.log('Processed enhanced chat response:', response)
      
      // Handle the response based on its format
      let userMessage: Message;
      let assistantMessage: Message;
      
      // Check if response has the expected structure with user_message and assistant_message
      if (response && typeof response === 'object' && 'user_message' in response && 'assistant_message' in response && 
          response.user_message && response.assistant_message) {
        // New format with saved messages
        userMessage = {
          id: response.user_message.message_id,
          sessionId: response.user_message.session_id,
          type: 'user' as const,
          content: response.user_message.content,
          timestamp: new Date(response.user_message.created_at)
        };
        
        assistantMessage = {
          id: response.assistant_message.message_id,
          sessionId: response.assistant_message.session_id,
          type: 'assistant' as const,
          content: response.assistant_message.content,
          timestamp: new Date(response.assistant_message.created_at),
          contextPassages: response.assistant_message.context_passages
        };
      } else {
        // Handle direct response format (answer, passages, etc.)
        // Fallback to old format (generate IDs client-side)
        userMessage = {
          id: UuidUtils.generateMessageId(),
          sessionId: sessionId,
          type: 'user',
          content: content,
          timestamp: new Date()
        };
        
        assistantMessage = {
          id: UuidUtils.generateMessageId(),
          sessionId: sessionId,
          type: 'assistant',
          content: response && typeof response === 'object' && 'answer' in response 
            ? response.answer 
            : 'Sorry, I couldn\'t process that request.',
          timestamp: new Date(),
          contextPassages: response && typeof response === 'object' && 'passages' in response 
            ? response.passages 
            : []
        };
      }
      
      setMessages(prev => [...prev, userMessage, assistantMessage])
      
      // Update session message count
      if (selectedSession) {
        setSessions(prev => prev.map(session =>
          session.id === selectedSession.id
            ? {
                ...session,
                messageCount: session.messageCount + 2,
                lastMessage: content
              }
            : session
        ))
      }
      
      return { userMessage, assistantMessage }
    } catch (error) {
      console.error('Failed to send enhanced message:', error)
      throw error
    }
  }, [selectedAssistant, selectedSession])

  // File management
  const addUploadedFile = useCallback((file: Omit<UploadedFile, 'id' | 'uploadedAt'>) => {
    const newFile: UploadedFile = {
      ...file,
      id: UuidUtils.generateV4(),
      uploadedAt: new Date()
    }

    setUploadedFiles(prev => [...prev, newFile])
    return newFile
  }, [])

  const removeUploadedFile = useCallback((fileId: string) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId))
  }, [])

  return {
    // State
    selectedAssistant,
    selectedSession,
    sessions,
    messages,
    uploadedFiles,
    loadingSessions,
    loadingMessages,

    // Actions
    selectAssistant,
    createNewSession,
    selectSession,
    addMessage,
    sendMessageToAssistant,
    sendEnhancedMessageToAssistant,
    addUploadedFile,
    removeUploadedFile
  }
}