import { Card, CardBody, Button, Popover, PopoverTrigger, PopoverContent } from '@heroui/react'
import { Heading, Text, Flex } from '@radix-ui/themes'
import { PaperPlaneIcon, ChatBubbleIcon, ClipboardIcon } from '@radix-ui/react-icons'
import { useState, useRef, useEffect } from 'react'
import { AnimatePresence } from 'framer-motion'
import { FileUpload } from '../../molecules'
import { ChatMessage } from '../../molecules/ChatMessage'
import { useTextareaAutoResize } from '../../../hooks/useTextareaAutoResize'
import type { FileUploadItem } from '../../molecules'
import type { Message, ChatSession } from '../../../hooks/useChatState'

// Type for messages that can be displayed in the chat (excluding system messages)
type DisplayableMessage = Omit<Message, 'type'> & {
  type: 'user' | 'assistant'
}

interface ChatAreaProps {
  className?: string
  selectedSession: ChatSession | null
  messages: Message[]
  onSendMessage: (content: string, files?: FileUploadItem[]) => void
  isSendingMessage?: boolean
}

export const ChatArea = ({ className, selectedSession, messages, onSendMessage, isSendingMessage = false }: ChatAreaProps) => {
  const [inputValue, setInputValue] = useState('')
  const [selectedFiles, setSelectedFiles] = useState<FileUploadItem[]>([])
  const [isFileUploadOpen, setIsFileUploadOpen] = useState(false)
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const textareaRef = useTextareaAutoResize(inputValue)

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }

  useEffect(() => {
    scrollToBottom()
  }, [messages])

  const handleSendMessage = async () => {
    if (!inputValue.trim() && selectedFiles.length === 0) return
    if (!selectedSession) return

    // Send message with files if any
    onSendMessage(inputValue.trim(), selectedFiles.length > 0 ? selectedFiles : undefined)

    // Clear input and files immediately since user message is shown right away
    setInputValue('')
    setSelectedFiles([])
    setIsFileUploadOpen(false)
  }

  const handleFilesSelected = (files: FileUploadItem[]) => {
    setSelectedFiles(prev => [...prev, ...files])
  }

  const handleRemoveFile = (fileId: string) => {
    setSelectedFiles(prev => prev.filter(file => file.id !== fileId))
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSendMessage()
    }
  }

  return (
    <div className={`h-full ${className || ''}`}>
      <Card className="h-full border border-gray-200 shadow-sm">
        <CardBody className="p-0 h-full flex flex-col">
          {/* Header */}
          <div className="p-6 border-b border-gray-200 bg-gray-50">
            <Flex align="center" gap="2">
              <ChatBubbleIcon className="w-5 h-5 text-indigo-600" />
              <Heading size="4" className="text-gray-900 font-bold">
                {selectedSession ? selectedSession.name : 'Conversation'}
              </Heading>
            </Flex>
            <Text className="text-gray-600 text-sm mt-1">
              {selectedSession
                ? 'Chat with your AI assistant'
                : 'Select a session to start chatting'
              }
            </Text>
          </div>

          {/* Messages Area */}
          <div className="flex-1 overflow-y-auto p-6">
            {!selectedSession ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <ChatBubbleIcon className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                  <Text className="text-gray-500 text-lg font-medium mb-2">
                    No Session Selected
                  </Text>
                  <Text className="text-gray-400 text-sm">
                    Create or select a chat session to start chatting
                  </Text>
                </div>
              </div>
            ) : messages.length === 0 ? (
              <div className="h-full flex items-center justify-center">
                <div className="text-center">
                  <ChatBubbleIcon className="w-12 h-12 text-gray-300 mx-auto mb-2" />
                  <Text className="text-gray-500 text-sm">
                    Start a conversation
                  </Text>
                  <Text className="text-gray-400 text-xs">
                    Ask anything about your knowledge bases
                  </Text>
                </div>
              </div>
            ) : (
              <div className="space-y-4">
                <AnimatePresence>
                  {messages
                    .filter(message => message.type !== 'system')
                    .map((message) => (
                      <ChatMessage key={message.id} message={message as DisplayableMessage} />
                    ))}
                </AnimatePresence>

                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Input Area */}
          <div className="p-6 border-t border-gray-200 bg-white">
            {/* File Upload Section */}
            {selectedFiles.length > 0 && (
              <div className="mb-4">
                <FileUpload
                  onFilesSelected={handleFilesSelected}
                  selectedFiles={selectedFiles}
                  onRemoveFile={handleRemoveFile}
                  maxFiles={3}
                />
              </div>
            )}

            <Flex gap="2" align="end">
              <div className="flex-1">
                <textarea
                  ref={textareaRef}
                  placeholder={selectedSession ? "Ask me anything about your knowledge bases..." : "Select a session to start chatting"}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  className="w-full p-3 border border-gray-300 rounded-md resize-none focus:outline-none focus:ring-2 focus:ring-indigo-500"
                  disabled={isSendingMessage || !selectedSession}
                  rows={1}
                />
              </div>

              {/* File Upload Button */}
              <Popover isOpen={isFileUploadOpen} onOpenChange={setIsFileUploadOpen}>
                <PopoverTrigger>
                  <Button
                    variant="bordered"
                    size="lg"
                    isIconOnly
                    isDisabled={!selectedSession}
                    className={selectedFiles.length > 0 ? 'border-indigo-500 text-indigo-600' : ''}
                  >
                    <ClipboardIcon className="w-4 h-4" />
                  </Button>
                </PopoverTrigger>
                <PopoverContent className="w-80">
                  <div className="p-4">
                    <Text className="text-sm font-medium mb-3">Upload Files</Text>
                    <FileUpload
                      onFilesSelected={handleFilesSelected}
                      selectedFiles={selectedFiles}
                      onRemoveFile={handleRemoveFile}
                      maxFiles={3}
                    />
                  </div>
                </PopoverContent>
              </Popover>

              {/* Send Button */}
              <Button
                color="primary"
                variant="solid"
                size="lg"
                onClick={handleSendMessage}
                isDisabled={(!inputValue.trim() && selectedFiles.length === 0) || !selectedSession}
                isIconOnly
              >
                <PaperPlaneIcon className="w-4 h-4" />
              </Button>
            </Flex>
            <Text className="text-xs text-gray-500 mt-2">
              {selectedSession
                ? "Press Enter to send, Shift+Enter for new line"
                : "Select a session to start chatting"
              }
            </Text>
          </div>
        </CardBody>
      </Card>
    </div>
  )
}