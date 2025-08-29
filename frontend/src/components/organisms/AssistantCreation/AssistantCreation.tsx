import { Card, CardBody, Button, Avatar, Chip } from '@heroui/react'
import { Heading, Text, Flex } from '@radix-ui/themes'
import { PlusIcon, PersonIcon, TrashIcon, GearIcon } from '@radix-ui/react-icons'
import { useState } from 'react'
import { CreateAssistantModal } from '../../molecules'
import { motion } from 'framer-motion'
import type { Assistant, ModelSettings } from '../../../hooks/useChatState'

interface AssistantData {
  name: string
  description: string
  knowledgeBases: string[]
  modelSettings: ModelSettings
}

interface AssistantCreationProps {
  className?: string
  onAssistantSelect?: (assistant: Assistant) => void
}

export const AssistantCreation = ({ className, onAssistantSelect }: AssistantCreationProps) => {
  const [isModalOpen, setIsModalOpen] = useState(false)
  const [assistants, setAssistants] = useState<Assistant[]>([])
  const [selectedAssistant, setSelectedAssistant] = useState<Assistant | null>(null)

  const knowledgeBases = [
    { id: '1', name: 'Product Documentation', docs: 156 },
    { id: '2', name: 'Technical Specifications', docs: 89 },
    { id: '3', name: 'User Manuals', docs: 234 },
    { id: '4', name: 'Research Papers', docs: 67 }
  ]

  // Animation variants
  const cardVariants = {
    hidden: { opacity: 0, y: 20 },
    visible: { opacity: 1, y: 0, transition: { duration: 0.3 } }
  }

  const handleCreateAssistant = (data: AssistantData) => {
    const newAssistant: Assistant = {
      id: Date.now().toString(),
      name: data.name,
      description: data.description,
      knowledgeBases: data.knowledgeBases,
      modelSettings: data.modelSettings,
      createdAt: new Date()
    }

    setAssistants(prev => [...prev, newAssistant])
  }

  const handleDeleteAssistant = (id: string) => {
    setAssistants(prev => prev.filter(assistant => assistant.id !== id))
  }

  const handleAssistantSelect = (assistant: Assistant) => {
    setSelectedAssistant(assistant)
    onAssistantSelect?.(assistant)
  }

  const getKnowledgeBaseNames = (ids: string[]) => {
    return ids.map(id => knowledgeBases.find(kb => kb.id === id)?.name).filter(Boolean).join(', ')
  }

  return (
    <div className={`h-full ${className || ''}`}>
      <Card className="h-full border border-gray-200 shadow-sm">
        <CardBody className="p-6">
          <Flex direction="column" gap="4" className="h-full">
            {/* Header */}
            <div>
              <Flex align="center" gap="2" className="mb-2">
                <PersonIcon className="w-5 h-5 text-indigo-600" />
                <Heading size="4" className="text-gray-900 font-bold">
                  AI Assistants
                </Heading>
              </Flex>
              <Text className="text-gray-600 text-sm">
                Create and manage your AI assistants
              </Text>
            </div>

            {/* Create Assistant Button */}
            <Button
              color="primary"
              variant="solid"
              size="md"
              startContent={<PlusIcon className="w-4 h-4" />}
              className="w-full font-medium"
              onClick={() => setIsModalOpen(true)}
            >
              Create Assistant
            </Button>

            {/* Assistants List */}
            <div className="flex-1 overflow-y-auto">
              {assistants.length === 0 ? (
                <div className="flex flex-col items-center justify-center h-32 text-center">
                  <PersonIcon className="w-12 h-12 text-gray-300 mb-2" />
                  <Text className="text-gray-500 text-sm">
                    No assistants created yet
                  </Text>
                  <Text className="text-gray-400 text-xs">
                    Click "Create Assistant" to get started
                  </Text>
                </div>
              ) : (
                <div className="space-y-3">
                  <Text className="text-sm font-medium text-gray-700 mb-3">
                    Your Assistants ({assistants.length})
                  </Text>
                  {assistants.map((assistant) => (
                    <motion.div
                      key={assistant.id}
                      variants={cardVariants}
                      initial="hidden"
                      animate="visible"
                      className={`p-4 rounded-lg border cursor-pointer hover:shadow-sm transition-all ${
                        selectedAssistant?.id === assistant.id
                          ? 'border-indigo-500 bg-indigo-50'
                          : 'bg-gray-50 border-gray-200 hover:border-gray-300'
                      }`}
                      onClick={() => handleAssistantSelect(assistant)}
                    >
                      <Flex align="center" justify="between" className="mb-2">
                        <Flex align="center" gap="3">
                          <Avatar
                            size="sm"
                            className="bg-indigo-600 text-white flex-shrink-0"
                            fallback={assistant.name.charAt(0).toUpperCase()}
                          />
                          <div className="flex-1 min-w-0">
                            <Text className="text-sm font-medium text-gray-900 truncate">
                              {assistant.name}
                            </Text>
                            <Text className="text-xs text-gray-500 truncate">
                              {assistant.description || 'No description'}
                            </Text>
                          </div>
                        </Flex>
                        <Button
                          size="sm"
                          variant="light"
                          color="danger"
                          isIconOnly
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDeleteAssistant(assistant.id)
                          }}
                        >
                          <TrashIcon className="w-4 h-4" />
                        </Button>
                      </Flex>
                      
                      {/* Model Settings Display */}
                      <div className="mb-2">
                        <Flex align="center" gap="2" className="mb-1">
                          <GearIcon className="w-3 h-3 text-gray-400" />
                          <Text className="text-xs text-gray-600">
                            Model: {assistant.modelSettings.model}
                          </Text>
                        </Flex>
                        <Flex gap="1" wrap="wrap">
                          <Chip size="sm" variant="flat" className="text-xs">
                            T: {assistant.modelSettings.temperature}
                          </Chip>
                          <Chip size="sm" variant="flat" className="text-xs">
                            P: {assistant.modelSettings.topP}
                          </Chip>
                        </Flex>
                      </div>
                      
                      <Text className="text-xs text-gray-500 truncate">
                        Knowledge: {getKnowledgeBaseNames(assistant.knowledgeBases)}
                      </Text>
                      <Text className="text-xs text-gray-400 mt-1">
                        Created: {assistant.createdAt.toLocaleDateString()}
                      </Text>
                    </motion.div>
                  ))}
                </div>
              )}
            </div>
          </Flex>
        </CardBody>
      </Card>

      {/* Create Assistant Modal */}
      <CreateAssistantModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onCreateAssistant={handleCreateAssistant}
        knowledgeBases={knowledgeBases}
      />
    </div>
  )
}