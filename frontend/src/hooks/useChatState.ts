import { useState, useCallback } from 'react'

export interface ModelSettings {
  model: string
  temperature: number
  topP: number
  presencePenalty: number
  frequencyPenalty: number
}

export interface Assistant {
  id: string
  name: string
  description: string
  knowledgeBases: string[]
  modelSettings: ModelSettings
  createdAt: Date
}

export interface ChatSession {
  id: string
  name: string
  assistantId: string
  createdAt: Date
  lastMessage?: string
  messageCount: number
}

export interface Message {
  id: string
  type: 'user' | 'assistant'
  content: string
  timestamp: Date
  sessionId: string
}

export interface UploadedFile {
  id: string
  name: string
  size: number
  type: string
  uploadedAt: Date
  url?: string
}

export const useChatState = () => {
  const [selectedAssistant, setSelectedAssistant] = useState<Assistant | null>(null)
  const [selectedSession, setSelectedSession] = useState<ChatSession | null>(null)
  const [sessions, setSessions] = useState<ChatSession[]>([])
  const [messages, setMessages] = useState<Message[]>([])
  const [uploadedFiles, setUploadedFiles] = useState<UploadedFile[]>([])

  // Assistant management
  const selectAssistant = useCallback((assistant: Assistant | null) => {
    setSelectedAssistant(assistant)
    setSelectedSession(null) // Clear selected session when changing assistant
    setMessages([]) // Clear messages when changing assistant

    // Filter sessions for the selected assistant
    if (assistant) {
      // Load sessions for this assistant (in real app, this would be an API call)
      const assistantSessions = sessions.filter(session => session.assistantId === assistant.id)
      // Auto-select first session if available
      if (assistantSessions.length > 0) {
        setSelectedSession(assistantSessions[0])
      }
    }
  }, [sessions])

  // Session management
  const createNewSession = useCallback((assistantId: string, sessionName?: string) => {
    if (!assistantId) return null

    const newSession: ChatSession = {
      id: Date.now().toString(),
      name: sessionName || `New Chat ${sessions.length + 1}`,
      assistantId,
      createdAt: new Date(),
      messageCount: 0
    }

    setSessions(prev => [...prev, newSession])
    setSelectedSession(newSession)
    setMessages([])
    return newSession
  }, [sessions.length])

  const selectSession = useCallback((session: ChatSession | null) => {
    setSelectedSession(session)
    if (session) {
      // Load messages for this session (in real app, this would be an API call)
      const sessionMessages = messages.filter(msg => msg.sessionId === session.id)
      setMessages(sessionMessages)
    } else {
      setMessages([])
    }
  }, [messages])

  // Message management
  const addMessage = useCallback((message: Omit<Message, 'id'>) => {
    const newMessage: Message = {
      ...message,
      id: Date.now().toString()
    }

    setMessages(prev => [...prev, newMessage])

    // Update session with last message and count
    if (selectedSession) {
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

    return newMessage
  }, [selectedSession])

  // File management
  const addUploadedFile = useCallback((file: Omit<UploadedFile, 'id' | 'uploadedAt'>) => {
    const newFile: UploadedFile = {
      ...file,
      id: Date.now().toString(),
      uploadedAt: new Date()
    }

    setUploadedFiles(prev => [...prev, newFile])
    return newFile
  }, [])

  const removeUploadedFile = useCallback((fileId: string) => {
    setUploadedFiles(prev => prev.filter(file => file.id !== fileId))
  }, [])

  // Get sessions for current assistant
  const currentAssistantSessions = sessions.filter(
    session => selectedAssistant && session.assistantId === selectedAssistant.id
  )

  return {
    // State
    selectedAssistant,
    selectedSession,
    sessions: currentAssistantSessions,
    messages,
    uploadedFiles,

    // Actions
    selectAssistant,
    createNewSession,
    selectSession,
    addMessage,
    addUploadedFile,
    removeUploadedFile
  }
}
