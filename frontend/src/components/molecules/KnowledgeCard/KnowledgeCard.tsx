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
  return (
    <Card 
      className={`p-6 hover:shadow-lg transition-all duration-200 border border-gray-200 hover:border-indigo-300 cursor-pointer ${className || ''}`}
      onClick={onClick}
    >
      <CardBody>
        <Heading size="4" className="text-gray-900 mb-3 line-clamp-1">
          {title}
        </Heading>
        
        <Text className="text-gray-600 leading-relaxed mb-4 line-clamp-2 min-h-[3rem]">
          {description}
        </Text>
        
        <Flex align="center" justify="between" className="text-sm text-gray-500">
          <Flex align="center" gap="2">
            <FileTextIcon className="w-4 h-4" />
            <span>{documentCount} documents</span>
          </Flex>
          
          <Flex align="center" gap="2">
            <ClockIcon className="w-4 h-4" />
            <span>{createdAt}</span>
          </Flex>
        </Flex>
      </CardBody>
    </Card>
  )
}