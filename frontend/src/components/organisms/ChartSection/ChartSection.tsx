import { Card, CardBody, Button } from '@heroui/react'
import { Heading, Text, Flex } from '@radix-ui/themes'
import { ChatBubbleIcon, PlusIcon, ClockIcon } from '@radix-ui/react-icons'
import type { Assistant, ChatSession } from '../../../hooks/useChatState'
import { useState, useEffect } from 'react'
import { ChatSessionSkeleton } from '../../atoms/ChatSessionSkeleton/ChatSessionSkeleton'

interface ChartSectionProps {
  className?: string
  selectedAssistant: Assistant | null
  sessions: ChatSession[]
  selectedSession: ChatSession | null
  onSelectSession: (session: ChatSession) => void
  onCreateNewSession: (assistantId: string, sessionName?: string) => Promise<void>
  loadingSessions?: boolean
}

export const ChartSection = ({
  className,
  selectedAssistant,
  sessions,
  selectedSession,
  onSelectSession,
  onCreateNewSession,
  loadingSessions = false
}: ChartSectionProps) => {
  const [isCreatingSession, setIsCreatingSession] = useState(false)
  const [isSwitchingSession, setIsSwitchingSession] = useState(false)
  const [previousSelectedSession, setPreviousSelectedSession] = useState<ChatSession | null>(null)

  // Handle session switching with loading effect
  useEffect(() => {
    if (selectedSession?.id !== previousSelectedSession?.id) {
      if (previousSelectedSession !== null) {
        // Only show loading when actually switching between sessions, not on initial load
        setIsSwitchingSession(true)
        const timer = setTimeout(() => {
          setIsSwitchingSession(false)
        }, 300) // 300ms loading effect
        return () => clearTimeout(timer)
      }
      setPreviousSelectedSession(selectedSession)
    }
  }, [selectedSession, previousSelectedSession])

  const handleCreateNewSession = async () => {
    if (selectedAssistant) {
      setIsCreatingSession(true)
      try {
        await onCreateNewSession(selectedAssistant.id)
      } finally {
        setIsCreatingSession(false)
      }
    }
  }

  const handleSelectSession = (session: ChatSession) => {
    setIsSwitchingSession(true)
    onSelectSession(session)
    // Simulate loading time for better UX
    setTimeout(() => {
      setIsSwitchingSession(false)
    }, 300)
  }

  return (
    <div className={`h-full ${className || ''}`}>
      <Card className="h-full border border-gray-200 shadow-sm">
        <CardBody className="p-6">
          <Flex direction="column" gap="4" className="h-full">
            {/* Header */}
            <div>
              <Flex align="center" gap="2" className="mb-2">
                <ChatBubbleIcon className="w-5 h-5 text-indigo-600" />
                <Heading size="4" className="text-gray-900 font-bold">
                  Chat Sessions
                </Heading>
              </Flex>
              <Text className="text-gray-600 text-sm">
                {selectedAssistant
                  ? `Sessions with ${selectedAssistant.name}`
                  : 'Select an assistant to view sessions'
                }
              </Text>
            </div>

            {selectedAssistant ? (
              <>
                {/* New Session Button */}
                <Button
                  color="primary"
                  variant="bordered"
                  size="sm"
                  startContent={<PlusIcon className="w-4 h-4" />}
                  className="w-full"
                  onClick={handleCreateNewSession}
                  isLoading={isCreatingSession}
                  disabled={isCreatingSession}
                >
                  {isCreatingSession ? 'Creating...' : 'New Chat Session'}
                </Button>

                {/* Sessions List */}
                <div className="flex-1 overflow-y-auto">
                  {loadingSessions || isSwitchingSession ? (
                    // Loading state when switching sessions or loading assistant sessions
                    <div className="space-y-2">
                      <div className="h-4 bg-gray-200 rounded w-1/3 mb-3 animate-pulse"></div>
                      {[...Array(3)].map((_, index) => (
                        <ChatSessionSkeleton key={index} />
                      ))}
                    </div>
                  ) : sessions.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-32 text-center">
                      <ChatBubbleIcon className="w-12 h-12 text-gray-300 mb-2" />
                      <Text className="text-gray-500 text-sm">
                        No chat sessions yet
                      </Text>
                      <Text className="text-gray-400 text-xs">
                        Create a new session to get started
                      </Text>
                    </div>
                  ) : (
                    <div className="space-y-2">
                      <Text className="text-sm font-medium text-gray-700 mb-3">
                        Recent Sessions ({sessions.length})
                      </Text>
                      {sessions.map((session) => (
                        <div
                          key={session.id}
                          className={`p-3 rounded-lg border cursor-pointer transition-all duration-200 ${
                            selectedSession?.id === session.id
                              ? 'border-indigo-500 bg-indigo-50 shadow-sm'
                              : 'border-gray-200 hover:border-gray-300 hover:bg-gray-50'
                          } ${
                            isSwitchingSession ? 'opacity-50' : ''
                          }`}
                          onClick={() => handleSelectSession(session)}
                        >
                          <Text className="text-sm font-medium text-gray-900 mb-1 line-clamp-1">
                            {session.name}
                          </Text>
                          <Flex align="center" justify="between" className="mb-1">
                            <Text className="text-xs text-gray-500">
                              {session.messageCount} messages
                            </Text>
                            <Flex align="center" gap="1">
                              <ClockIcon className="w-3 h-3 text-gray-400" />
                              <Text className="text-xs text-gray-400">
                                {session.createdAt.toLocaleDateString()}
                              </Text>
                            </Flex>
                          </Flex>
                          {session.lastMessage && (
                            <Text className="text-xs text-gray-500 line-clamp-1">
                              "{session.lastMessage}"
                            </Text>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              </>
            ) : (
              <div className="flex-1 flex items-center justify-center">
                <div className="text-center">
                  <ChatBubbleIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <Text className="text-gray-500 text-lg font-medium mb-2">
                    No Assistant Selected
                  </Text>
                  <Text className="text-gray-400 text-sm">
                    Choose an assistant from the left panel to start chatting
                  </Text>
                </div>
              </div>
            )}
          </Flex>
        </CardBody>
      </Card>
    </div>
  )
}