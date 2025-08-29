import { Button, Modal, ModalContent, ModalHeader, ModalBody, ModalFooter, Tabs, Tab } from '@heroui/react'
import { Flex } from '@radix-ui/themes'
import { PersonIcon } from '@radix-ui/react-icons'
import { useState, useEffect } from 'react'
import { AssistantSettingsTab, ModelSettingsTab } from '../../atoms'

interface ModelSettings {
  model: string
  temperature: number
  topP: number
  presencePenalty: number
  frequencyPenalty: number
}

interface AssistantData {
  name: string
  description: string
  knowledgeBases: string[]
  modelSettings: ModelSettings
}

interface CreateAssistantModalProps {
  isOpen: boolean
  onClose: () => void
  onCreateAssistant: (data: AssistantData) => void
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
  const [activeTab, setActiveTab] = useState('assistant')
  const [assistantName, setAssistantName] = useState('')
  const [assistantDescription, setAssistantDescription] = useState('')
  const [selectedKnowledge, setSelectedKnowledge] = useState<string>('')
  
  // Model settings with defaults
  const [modelSettings, setModelSettings] = useState<ModelSettings>({
    model: 'gpt-4o',
    temperature: 0.7,
    topP: 1.0,
    presencePenalty: 0.0,
    frequencyPenalty: 0.0
  })

  const availableModels = [
    { key: 'gpt-4o', label: 'GPT-4o (Latest)' },
    { key: 'gpt-4-turbo', label: 'GPT-4 Turbo' },
    { key: 'gpt-3.5-turbo', label: 'GPT-3.5 Turbo' },
    { key: 'claude-3-opus', label: 'Claude 3 Opus' },
    { key: 'claude-3-sonnet', label: 'Claude 3 Sonnet' }
  ]

  // Reset form when modal closes
  useEffect(() => {
    if (!isOpen) {
      setActiveTab('assistant')
      setAssistantName('')
      setAssistantDescription('')
      setSelectedKnowledge('')
      setModelSettings({
        model: 'gpt-4o',
        temperature: 0.7,
        topP: 1.0,
        presencePenalty: 0.0,
        frequencyPenalty: 0.0
      })
    }
  }, [isOpen])

  const handleCreateAssistant = () => {
    if (!assistantName.trim() || !selectedKnowledge) return
    
    const assistantData: AssistantData = {
      name: assistantName.trim(),
      description: assistantDescription.trim(),
      knowledgeBases: [selectedKnowledge], // Convert single selection to array
      modelSettings
    }
    
    onCreateAssistant(assistantData)
    onClose()
  }

  const updateModelSetting = (key: keyof ModelSettings, value: string | number) => {
    setModelSettings(prev => ({ ...prev, [key]: value }))
  }

  return (
    <Modal 
      isOpen={isOpen} 
      onClose={onClose}
      size="3xl"
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
          <Tabs 
            selectedKey={activeTab} 
            onSelectionChange={(key) => setActiveTab(key as string)}
            className="w-full"
          >
            <Tab key="assistant" title="Assistant Settings">
              <AssistantSettingsTab
                assistantName={assistantName}
                assistantDescription={assistantDescription}
                selectedKnowledge={selectedKnowledge}
                knowledgeBases={knowledgeBases}
                onNameChange={setAssistantName}
                onDescriptionChange={setAssistantDescription}
                onKnowledgeChange={setSelectedKnowledge}
              />
            </Tab>

            <Tab key="model" title="Model Settings">
              <ModelSettingsTab
                modelSettings={modelSettings}
                availableModels={availableModels}
                onModelSettingChange={updateModelSetting}
              />
            </Tab>
          </Tabs>
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
            isDisabled={!assistantName.trim() || !selectedKnowledge}
          >
            Create Assistant
          </Button>
        </ModalFooter>
      </ModalContent>
    </Modal>
  )
}