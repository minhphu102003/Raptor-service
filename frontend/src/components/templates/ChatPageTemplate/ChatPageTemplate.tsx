import { Flex } from '@radix-ui/themes'
import { KnowledgeHeader } from '../../organisms'
import { AssistantCreation, ChatArea, ChartSection } from '../../organisms'
import { useChatState, type Assistant } from '../../../hooks/useChatState'
import type { FileUploadItem } from '../../molecules'

interface ChatPageTemplateProps {
  className?: string
}

export const ChatPageTemplate = ({ className }: ChatPageTemplateProps) => {
  const {
    selectedAssistant,
    selectedSession,
    sessions,
    messages,
    selectAssistant,
    createNewSession,
    selectSession,
    addMessage
  } = useChatState()

  // Handle assistant selection from AssistantCreation
  const handleAssistantSelect = (assistant: Assistant) => {
    selectAssistant(assistant)
    // Auto-create first session if none exists
    if (sessions.length === 0) {
      createNewSession(assistant.id, `Chat with ${assistant.name}`)
    }
  }

  // Handle message sending from ChatArea
  const handleSendMessage = (content: string, files?: FileUploadItem[]) => {
    if (!selectedSession) return

    // Add user message
    addMessage({
      type: 'user',
      content,
      timestamp: new Date(),
      sessionId: selectedSession.id
    })

    setTimeout(() => {
      let responseContent = 'I understand your question. Based on the available knowledge bases, I can help you with that.'
      
      if (files && files.length > 0) {
        const fileNames = files.map(f => f.name).join(', ')
        responseContent += ` I can also see you've uploaded: ${fileNames}. Let me analyze these files along with the relevant documents.`
      }
      
      addMessage({
        type: 'assistant',
        content: responseContent,
        timestamp: new Date(),
        sessionId: selectedSession.id
      })
    }, 1500)
  }
  return (
    <div className={`min-h-screen bg-gray-50 ${className || ''}`}>
      {/* Header */}
      <KnowledgeHeader />
      
      {/* Main Chat Interface - 3 Column Layout */}
      <div className="px-6 py-6">
        <Flex gap="6" className="h-[calc(100vh-120px)] w-full">
          {/* Left Section - Create Assistant (25% width) */}
          <div className="flex-1 min-w-0">
            <AssistantCreation onAssistantSelect={handleAssistantSelect} />
          </div>
          
          {/* Middle Section - Chart (25% width) */}
          <div className="flex-1 min-w-0">
            <ChartSection 
              selectedAssistant={selectedAssistant}
              sessions={sessions}
              selectedSession={selectedSession}
              onSelectSession={selectSession}
              onCreateNewSession={createNewSession}
            />
          </div>
          
          {/* Right Section - ChatArea (50% width - 2x wider) */}
          <div className="flex-[2] min-w-0">
            <ChatArea 
              selectedSession={selectedSession}
              messages={messages}
              onSendMessage={handleSendMessage}
            />
          </div>
        </Flex>
      </div>
    </div>
  )
}