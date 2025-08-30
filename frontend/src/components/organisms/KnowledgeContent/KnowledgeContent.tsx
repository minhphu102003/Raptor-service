import { Container, Section } from '@radix-ui/themes'
import { CreateKnowledgeModal, SearchAndCreateBar, KnowledgeCardsGrid } from '../../molecules'
import { WelcomeSection, EmptyState } from '../../atoms'
import { knowledgeBasesData } from '../../../constants/knowledgeData'
import { type CreateKnowledgeFormData } from '../../../schemas'
import { useState } from 'react'
import { motion } from 'framer-motion'

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

  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        duration: 0.6,
        staggerChildren: 0.1
      }
    }
  }

  const handleCreateKnowledge = async (data: CreateKnowledgeFormData) => {
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
        <motion.div
          variants={containerVariants}
          initial="hidden"
          animate="visible"
        >
          {/* Welcome Section */}
          <WelcomeSection userName={userName} />

          {/* Search and Create Section */}
          <SearchAndCreateBar
            searchQuery={searchQuery}
            onSearchChange={setSearchQuery}
            onCreateClick={() => setIsCreateModalOpen(true)}
          />

          {/* Knowledge Cards Grid */}
          <KnowledgeCardsGrid knowledgeBases={filteredKnowledgeBases} />

          {/* Empty State */}
          {filteredKnowledgeBases.length === 0 && (
            <EmptyState
              searchQuery={searchQuery}
              onClearSearch={() => setSearchQuery('')}
            />
          )}
        </motion.div>
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
