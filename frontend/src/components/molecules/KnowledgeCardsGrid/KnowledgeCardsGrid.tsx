import { KnowledgeCard } from '../KnowledgeCard'
import { motion } from 'framer-motion'

interface KnowledgeBase {
  id: string
  title: string
  description: string
  documentCount: number
  createdAt: string
}

interface KnowledgeCardsGridProps {
  knowledgeBases: KnowledgeBase[]
  className?: string
}

export const KnowledgeCardsGrid = ({ knowledgeBases, className }: KnowledgeCardsGridProps) => {
  const cardVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        duration: 0.4
      }
    }
  }

  return (
    <motion.div
      className={`grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6 ${className || ''}`}
      variants={{
        visible: {
          transition: {
            staggerChildren: 0.1,
            delayChildren: 0.3
          }
        }
      }}
    >
      {knowledgeBases.map((kb) => (
        <motion.div
          key={kb.id}
          variants={cardVariants}
          whileHover={{
            scale: 1.02,
            transition: { duration: 0.2 }
          }}
          whileTap={{ scale: 0.98 }}
        >
          <KnowledgeCard
            id={kb.id}
            title={kb.title}
            description={kb.description}
            documentCount={kb.documentCount}
            createdAt={kb.createdAt}
          />
        </motion.div>
      ))}
    </motion.div>
  )
}
