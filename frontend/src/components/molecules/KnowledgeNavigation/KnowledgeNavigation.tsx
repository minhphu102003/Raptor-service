import { Button } from '@heroui/react'
import { Flex } from '@radix-ui/themes'
import { useState } from 'react'
import { 
  FileTextIcon, 
  MagnifyingGlassIcon, 
  ChatBubbleIcon 
} from '@radix-ui/react-icons'

interface KnowledgeNavigationProps {
  className?: string
}

const navigationItems = [
  { 
    id: 'knowledge-base', 
    label: 'Knowledge Base', 
    icon: FileTextIcon,
    active: true 
  },
  { 
    id: 'search', 
    label: 'Search', 
    icon: MagnifyingGlassIcon,
    active: false 
  },
  { 
    id: 'agent', 
    label: 'Agent', 
    icon: ChatBubbleIcon,
    active: false 
  }
]

export const KnowledgeNavigation = ({ className }: KnowledgeNavigationProps) => {
  const [activeItem, setActiveItem] = useState('knowledge-base')

  return (
    <Flex align="center" gap="3" className={className}>
      {navigationItems.map((item) => {
        const IconComponent = item.icon
        return (
          <Button
            key={item.id}
            variant={activeItem === item.id ? "solid" : "ghost"}
            color={activeItem === item.id ? "primary" : "default"}
            size="md"
            startContent={<IconComponent className="w-4 h-4" />}
            className={`
              px-4 py-2 font-bold border-transparent rounded-md transition-colors
              ${activeItem === item.id 
                ? 'bg-indigo-600 text-white shadow-md' 
                : 'text-gray-600 hover:text-gray-900 hover:bg-gray-100'
              }
            `}
            onClick={() => setActiveItem(item.id)}
          >
            {item.label}
          </Button>
        )
      })}
    </Flex>
  )
}