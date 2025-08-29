import { Card, CardBody } from '@heroui/react'
import { Heading, Text, Flex } from '@radix-ui/themes'
import { ClockIcon, FileTextIcon } from '@radix-ui/react-icons'

interface KnowledgeCardProps {
  title: string
  description: string
  documentCount: number
  createdAt: string
  className?: string
  onClick?: () => void
}

export const KnowledgeCard = ({ 
  title, 
  description, 
  documentCount, 
  createdAt, 
  className,
  onClick 
}: KnowledgeCardProps) => {

  const formatTimestamp = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  return (
    <Card 
      className={`px-6 py-4 hover:shadow-lg transition-all duration-200 border border-gray-200 hover:border-indigo-300 cursor-pointer ${className || ''}`}
      onClick={onClick}
    >
      <CardBody>
        <Heading size="4" className="text-gray-900 font-bold mb-3 line-clamp-1" style={{ color: '#1f2937' }}>
          {title}
        </Heading>
        
        <Text className="text-gray-600 leading-relaxed mb-4 line-clamp-2 min-h-[3rem]">
          {description}
        </Text>
        
        <Flex align="start" direction={"column"} justify="between" gap={"2"} className="text-base text-gray-500">
          <Flex gap="1">
            <Flex align="center" gap="2">
              <FileTextIcon className="w-4 h-4" />
              <span>{documentCount} documents</span>
            </Flex>
          </Flex>
          
          <Flex gap="1">
            <Flex align="center" gap="2">
              <ClockIcon className="w-4 h-4" />
              <span>{formatTimestamp(createdAt)}</span>
            </Flex>
          </Flex>
        </Flex>
      </CardBody>
    </Card>
  )
}