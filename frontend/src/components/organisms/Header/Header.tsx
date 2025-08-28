import { Button } from '@heroui/react'
import { Container, Flex } from '@radix-ui/themes'
import { Logo } from '../../atoms'
import { Navigation } from '../../molecules'

interface HeaderProps {
  className?: string
}

export const Header = ({ className }: HeaderProps) => {
  return (
    <header className={`sticky top-0 z-50 backdrop-blur-sm bg-white/80 border-b border-gray-200 ${className || ''}`}>
      <Container size="4">
        <Flex align="center" justify="between" className="py-4">
          <Logo />
          
          <Flex align="center" gap="4">
            <Navigation />
            <Button color="primary" variant="solid" className="font-medium">
              Get Started
            </Button>
          </Flex>
        </Flex>
      </Container>
    </header>
  )
}