import { Flex } from '@radix-ui/themes'
import { KnowledgeHeader } from '../../organisms'
import { AssistantCreation, ChatArea, ChartSection } from '../../organisms'
import { useChatState, type ChatSession } from '../../../hooks/useChatState'
import type { FileUploadItem } from '../../molecules'
import { motion } from 'framer-motion'
import type { Assistant as ServiceAssistant } from '../../../services/assistantService'
import { useState, useEffect } from 'react'

interface ChatPageTemplateProps {
  className?: string
}

// Helper function to convert ServiceAssistant to ChatState Assistant
const convertServiceAssistantToChatAssistant = (serviceAssistant: ServiceAssistant) => {
  return {
    id: serviceAssistant.assistant_id,
    user_id: serviceAssistant.user_id,
    name: serviceAssistant.name,
    description: serviceAssistant.description || '',
    knowledgeBases: serviceAssistant.knowledge_bases,
    modelSettings: serviceAssistant.model_settings,
    systemPrompt: serviceAssistant.system_prompt,
    status: serviceAssistant.status,
    meta: serviceAssistant.meta,
    createdAt: serviceAssistant.created_at,
    updatedAt: serviceAssistant.updated_at || serviceAssistant.created_at,
    datasets: serviceAssistant.datasets
  }
}

export const ChatPageTemplate = ({ className }: ChatPageTemplateProps) => {
  const {
    selectedAssistant,
    selectedSession,
    sessions,
    messages,
    loadingSessions,
    loadingMessages,
    selectAssistant,
    createNewSession,
    selectSession,
    addMessage,
    sendMessageToAssistant,
    sendEnhancedMessageToAssistant
  } = useChatState()
  
  const [isSwitchingSession, setIsSwitchingSession] = useState(false)
  const [previousSelectedSession, setPreviousSelectedSession] = useState<string | null>(null)

  // Handle session switching with loading effect
  useEffect(() => {
    if (selectedSession?.id !== previousSelectedSession) {
      if (previousSelectedSession !== null) {
        // Only show loading when actually switching between sessions, not on initial load
        setIsSwitchingSession(true)
        const timer = setTimeout(() => {
          setIsSwitchingSession(false)
        }, 300) // 300ms loading effect
        return () => clearTimeout(timer)
      }
      setPreviousSelectedSession(selectedSession?.id || null)
    }
  }, [selectedSession, previousSelectedSession])

  // Animation variants
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        duration: 0.4,
        staggerChildren: 0.2
      }
    }
  }

  const sectionVariants = {
    hidden: { opacity: 0, y: 30 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.6,
        ease: "easeOut" as const
      }
    }
  }

  const headerVariants = {
    hidden: { opacity: 0, y: -20 },
    visible: {
      opacity: 1,
      y: 0,
      transition: {
        duration: 0.5,
        ease: "easeOut" as const
      }
    }
  }

  // Handle assistant selection from AssistantCreation
  const handleAssistantSelect = (assistant: ServiceAssistant) => {
    const convertedAssistant = convertServiceAssistantToChatAssistant(assistant)
    selectAssistant(convertedAssistant)
    // Sessions will be loaded automatically by the useChatState hook based on the selected assistant
  }

  // Handle session selection with loading effect
  const handleSelectSession = (session: ChatSession | null) => {
    setIsSwitchingSession(true)
    selectSession(session)
    // Simulate loading time for better UX
    setTimeout(() => {
      setIsSwitchingSession(false)
      setPreviousSelectedSession(session?.id || null)
    }, 300)
  }

  // Wrapper for createNewSession to match expected signature
  const handleCreateNewSession = async (assistantId: string, sessionName?: string) => {
    await createNewSession(assistantId, sessionName)
  }

  // Handle message sending from ChatArea
  const handleSendMessage = async (content: string, files?: FileUploadItem[]) => {
    if (!content.trim()) return;
    
    if (!selectedSession || !selectedAssistant) {
      // If there's no session yet, create one with the first message as title
      if (selectedAssistant) {
        const truncatedTitle = content.length > 50 
          ? content.substring(0, 47) + '...' 
          : content
        
        const newSession = await createNewSession(selectedAssistant.id, truncatedTitle)
        if (newSession) {
          // After creating the session, add the message
          addMessage({
            type: 'user',
            content,
            timestamp: new Date(),
            sessionId: newSession.id
          })
        }
      }
      return
    }

    // Note: We no longer set isSendingMessage here since the user message is shown immediately
    // and the send button is re-enabled for the next message
    
    try {
      // Send message to assistant using the new API
      if (files && files.length > 0) {
        // If files are attached, use enhanced messaging
        const fileNames = files.map(f => f.name).join(', ')
        const additionalContext = {
          uploadedFiles: fileNames
        }
        
        await sendEnhancedMessageToAssistant(
          content,
          selectedSession.id,
          selectedAssistant.knowledgeBases[0],
          additionalContext
        )
      } else {
        // Regular messaging
        await sendMessageToAssistant(
          content,
          selectedSession.id,
          selectedAssistant.knowledgeBases[0]
        )
      }
    } catch (error) {
      console.error('Failed to send message:', error)
      // Error message is now handled in the hook, so we don't need to add it here
    }
  }
  
  return (
    <div className={`min-h-screen bg-gray-50 ${className || ''}`}>
      {/* Header */}
      <motion.div
        variants={headerVariants}
        initial="hidden"
        animate="visible"
      >
        <KnowledgeHeader />
      </motion.div>

      {/* Main Chat Interface - 3 Column Layout */}
      <motion.div
        className="px-6 py-6"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        <Flex gap="6" className="h-[calc(100vh-120px)] w-full">
          {/* Left Section - Create Assistant (25% width) */}
          <motion.div
            className="flex-1 min-w-0"
            variants={sectionVariants}
            whileHover={{ scale: 1.01 }}
            transition={{ duration: 0.2 }}
          >
            <AssistantCreation onAssistantSelect={handleAssistantSelect} />
          </motion.div>

          {/* Middle Section - Chart (25% width) */}
          <motion.div
            className="flex-1 min-w-0"
            variants={sectionVariants}
            whileHover={{ scale: 1.01 }}
            transition={{ duration: 0.2 }}
          >
            <ChartSection
              selectedAssistant={selectedAssistant}
              sessions={sessions}
              selectedSession={selectedSession}
              loadingSessions={loadingSessions}
              onSelectSession={handleSelectSession}
              onCreateNewSession={handleCreateNewSession}
            />
          </motion.div>

          {/* Right Section - ChatArea (50% width - 2x wider) */}
          <motion.div
            className="flex-[2] min-w-0"
            variants={sectionVariants}
            whileHover={{ scale: 1.005 }}
            transition={{ duration: 0.2 }}
          >
            {isSwitchingSession || loadingMessages ? (
              // Loading state when switching sessions or loading messages
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">
                    {isSwitchingSession ? 'Loading conversation...' : 'Loading messages...'}
                  </p>
                </div>
              </div>
            ) : (
              <ChatArea
                selectedSession={selectedSession}
                messages={messages}
                onSendMessage={handleSendMessage}
              />
            )}
          </motion.div>
        </Flex>
      </motion.div>
    </div>
  )
}