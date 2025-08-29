import { 
  Modal, 
  ModalContent, 
  ModalHeader, 
  ModalBody, 
  ModalFooter, 
  Button, 
  Input,
  Textarea
} from '@heroui/react'
import { Text } from '@radix-ui/themes'
import { useState, useEffect } from 'react'

export interface CreateKnowledgeModalProps {
  isOpen: boolean
  onClose: () => void
  onSubmit: (data: { name: string; description: string }) => void
}

export const CreateKnowledgeModal = ({ isOpen, onClose, onSubmit }: CreateKnowledgeModalProps) => {
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  // Reset state when modal closes
  useEffect(() => {
    if (!isOpen) {
      setName('')
      setDescription('')
      setIsSubmitting(false)
    }
  }, [isOpen])

  const handleSubmit = async () => {
    if (!name.trim()) return

    setIsSubmitting(true)
    try {
      await onSubmit({
        name: name.trim(),
        description: description.trim()
      })
      onClose()
    } catch (error) {
      console.error('Error creating knowledge base:', error)
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleClose = () => {
    if (!isSubmitting) {
      onClose()
    }
  }

  const isValid = name.trim().length > 0

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={handleClose}
      size="md"
      placement="center"
      backdrop="blur"
      classNames={{
        closeButton: "text-xl p-2 m-2"
      }}
    >
      <ModalContent>
        <ModalHeader className="flex flex-col gap-1">
          <h2 className="text-xl font-bold text-gray-900">Create New Knowledge Base</h2>
          <Text size="2" className="text-gray-600">
            Create a new knowledge base to organize your documents
          </Text>
        </ModalHeader>
        
        <ModalBody className="py-6">
          <div className="space-y-4">
            <div>
              <Input
                label="Name"
                placeholder="Enter a name for your knowledge base"
                value={name}
                onChange={(e) => setName(e.target.value)}
                variant="bordered"
                size="lg"
                isRequired
                autoFocus
                disabled={isSubmitting}
                className="w-full"
              />
            </div>
            
            <div>
              <Textarea
                label="Description"
                placeholder="Describe what this knowledge base contains..."
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                variant="bordered"
                size="lg"
                minRows={3}
                maxRows={5}
                disabled={isSubmitting}
                className="w-full"
              />
            </div>
          </div>
        </ModalBody>
        
        <ModalFooter>
          <Button 
            variant="ghost" 
            onPress={handleClose}
            disabled={isSubmitting}
          >
            Cancel
          </Button>
          <Button 
            color="primary" 
            onPress={handleSubmit}
            disabled={!isValid || isSubmitting}
            isLoading={isSubmitting}
          >
            {isSubmitting ? 'Creating...' : 'Create Knowledge Base'}
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  )
}