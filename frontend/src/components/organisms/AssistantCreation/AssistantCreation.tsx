import { Card, CardBody, Button, Avatar } from '@heroui/react'
import { Heading, Text, Flex } from '@radix-ui/themes'
import { PlusIcon, PersonIcon, TrashIcon } from '@radix-ui/react-icons'
import { useState } from 'react'
import { CreateAssistantModal } from '../../molecules'

interface Assistant {
  id: string
  name: string
  description: string
  knowledgeBases: string[]
  createdAt: Date
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

  const handleCreateAssistant = (name: string, description: string, knowledgeBases: string[]) => {
    const newAssistant: Assistant = {
      id: Date.now().toString(),
      name,
      description,
      knowledgeBases,
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
                    <div
                      key={assistant.id}
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
                          <div>
                            <Text className="text-sm font-medium text-gray-900">
                              {assistant.name}
                            </Text>
                            <Text className="text-xs text-gray-500">
                              {assistant.description || 'No description'}
                            </Text>
                          </div>
                        </Flex>
                        <Button
                          size="sm"
                          variant="light"
                          color="danger"
                          isIconOnly
                          onClick={() => handleDeleteAssistant(assistant.id)}
                        >
                          <TrashIcon className="w-4 h-4" />
                        </Button>
                      </Flex>
                      <Text className="text-xs text-gray-500">
                        Knowledge: {getKnowledgeBaseNames(assistant.knowledgeBases)}
                      </Text>
                      <Text className="text-xs text-gray-400 mt-1">
                        Created: {assistant.createdAt.toLocaleDateString()}
                      </Text>
                    </div>
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