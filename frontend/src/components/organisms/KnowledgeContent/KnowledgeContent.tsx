import { Button, Input } from '@heroui/react'
import { Container, Heading, Text, Section } from '@radix-ui/themes'
import { MagnifyingGlassIcon, PlusIcon } from '@radix-ui/react-icons'
import { KnowledgeCard, CreateKnowledgeModal } from '../../molecules'
import { knowledgeBasesData } from '../../../constants/knowledgeData'
import { useState } from 'react'

interface KnowledgeContentProps {
  userName?: string
  className?: string
}

export const KnowledgeContent = ({ userName = 'John', className }: KnowledgeContentProps) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [isCreateModalOpen, setIsCreateModalOpen] = useState(false)
  
  const filteredKnowledgeBases = knowledgeBasesData.filter(kb =>
    kb.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
    kb.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  const handleCreateKnowledge = async (data: { name: string; description: string }) => {
    try {
      // TODO: Implement API call to create knowledge base
      console.log('Creating knowledge base:', data)
      
      // For now, just log the data
      // In a real implementation, you would call an API here
      // await createKnowledgeBase(data)
      
      // Show success message or update the list
      alert(`Knowledge base "${data.name}" created successfully!`)
    } catch (error) {
      console.error('Failed to create knowledge base:', error)
      throw error // Re-throw to let the modal handle the error state
    }
  }

  return (
    <Section className={`py-8 ${className || ''}`}>
      <Container size="4">
        {/* Welcome Section */}
        <div className="mb-8">
          <Heading as="h3" size="9" className="text-gray-900 mb-2 text-2xl lg:text-5xl">
            Welcome back, <span className="username-emphasis">{userName}</span>!
          </Heading>
          <Text size="5" className="text-gray-600">
            Manage your knowledge bases and explore your documents
          </Text>
        </div>

        {/* Search and Create Section */}
        <div className="flex flex-col sm:flex-row gap-4 mb-8">
          <div className="flex-1">
            <Input
              placeholder="Search knowledge bases..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              startContent={<MagnifyingGlassIcon className="w-4 h-4 text-gray-400" />}
              className="w-full"
              size="lg"
            />
          </div>
          <Button
            color="primary"
            size="lg"
            startContent={<PlusIcon className="w-4 h-4" />}
            className="sm:w-auto w-full"
            onPress={() => setIsCreateModalOpen(true)}
          >
            Create Knowledge Base
          </Button>
        </div>

        {/* Knowledge Cards Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {filteredKnowledgeBases.map((kb) => (
            <KnowledgeCard
              key={kb.id}
              id={kb.id}
              title={kb.title}
              description={kb.description}
              documentCount={kb.documentCount}
              createdAt={kb.createdAt}
            />
          ))}
        </div>

        {/* Empty State */}
        {filteredKnowledgeBases.length === 0 && (
          <div className="text-center py-12">
            <Text size="4" className="text-gray-500 mb-4">
              No knowledge bases found matching "{searchQuery}"
            </Text>
            <Button
              variant="ghost"
              onClick={() => setSearchQuery('')}
            >
              Clear search
            </Button>
          </div>
        )}
      </Container>

      {/* Create Knowledge Modal */}
      <CreateKnowledgeModal
        isOpen={isCreateModalOpen}
        onClose={() => setIsCreateModalOpen(false)}
        onSubmit={handleCreateKnowledge}
      />
    </Section>
  )
}