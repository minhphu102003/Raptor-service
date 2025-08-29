import { Button, Input, Textarea, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter } from '@heroui/react'
import { Text, Flex } from '@radix-ui/themes'
import { PersonIcon } from '@radix-ui/react-icons'
import { useState, useEffect } from 'react'

interface CreateAssistantModalProps {
  isOpen: boolean
  onClose: () => void
  onCreateAssistant: (name: string, description: string, knowledgeBases: string[]) => void
  knowledgeBases: Array<{ id: string; name: string; docs: number }>
  className?: string
}

export const CreateAssistantModal = ({ 
  isOpen, 
  onClose, 
  onCreateAssistant, 
  knowledgeBases,
  className 
}: CreateAssistantModalProps) => {
  const [assistantName, setAssistantName] = useState('')
  const [assistantDescription, setAssistantDescription] = useState('')
  const [selectedKnowledge, setSelectedKnowledge] = useState<string[]>([])

  // Reset form when modal closes
  useEffect(() => {
    if (!isOpen) {
      setAssistantName('')
      setAssistantDescription('')
      setSelectedKnowledge([])
    }
  }, [isOpen])

  const toggleKnowledgeBase = (id: string) => {
    setSelectedKnowledge(prev => 
      prev.includes(id) 
        ? prev.filter(item => item !== id)
        : [...prev, id]
    )
  }

  const handleCreateAssistant = () => {
    if (!assistantName.trim() || selectedKnowledge.length === 0) return
    
    onCreateAssistant(assistantName.trim(), assistantDescription.trim(), selectedKnowledge)
    onClose()
  }

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose}
      size="2xl"
      className={className}
    >
      <ModalContent>
        <ModalHeader className="flex flex-col gap-1">
          <Flex align="center" gap="2">
            <PersonIcon className="w-5 h-5 text-indigo-600" />
            <span>Create New Assistant</span>
          </Flex>
        </ModalHeader>
        <ModalBody>
          <div className="space-y-4">
            {/* Assistant Configuration */}
            <div>
              <Text className="text-sm font-medium text-gray-700 mb-2">
                Assistant Name *
              </Text>
              <Input
                placeholder="Enter assistant name"
                value={assistantName}
                onChange={(e) => setAssistantName(e.target.value)}
                variant="bordered"
                size="md"
              />
            </div>

            <div>
              <Text className="text-sm font-medium text-gray-700 mb-2">
                Description
              </Text>
              <Textarea
                placeholder="Describe your assistant's purpose..."
                value={assistantDescription}
                onChange={(e) => setAssistantDescription(e.target.value)}
                variant="bordered"
                size="md"
                minRows={3}
              />
            </div>

            {/* Knowledge Base Selection */}
            <div>
              <Text className="text-sm font-medium text-gray-700 mb-3">
                Select Knowledge Bases *
              </Text>
              <div className="space-y-2 max-h-48 overflow-y-auto">
                {knowledgeBases.map((kb) => (
                  <div
                    key={kb.id}
                    className={`p-3 rounded-lg border cursor-pointer transition-colors ${
                      selectedKnowledge.includes(kb.id)
                        ? 'border-indigo-500 bg-indigo-50'
                        : 'border-gray-200 hover:border-gray-300'
                    }`}
                    onClick={() => toggleKnowledgeBase(kb.id)}
                  >
                    <Flex align="center" justify="between">
                      <div>
                        <Text className="text-sm font-medium text-gray-900">
                          {kb.name}
                        </Text>
                        <Text className="text-xs text-gray-500">
                          {kb.docs} documents
                        </Text>
                      </div>
                      <div className={`w-4 h-4 rounded border-2 ${
                        selectedKnowledge.includes(kb.id)
                          ? 'border-indigo-500 bg-indigo-500'
                          : 'border-gray-300'
                      }`}>
                        {selectedKnowledge.includes(kb.id) && (
                          <div className="w-full h-full flex items-center justify-center">
                            <div className="w-2 h-2 bg-white rounded-full" />
                          </div>
                        )}
                      </div>
                    </Flex>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </ModalBody>
        <ModalFooter>
          <Button 
            color="danger" 
            variant="light" 
            onClick={onClose}
          >
            Cancel
          </Button>
          <Button 
            color="primary" 
            onClick={handleCreateAssistant}
            isDisabled={!assistantName.trim() || selectedKnowledge.length === 0}
          >
            Create Assistant
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  )
}