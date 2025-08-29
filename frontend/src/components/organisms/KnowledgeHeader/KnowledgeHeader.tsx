import { Container, Flex } from '@radix-ui/themes'
import { Logo, LanguageSelector, ThemeToggle, UserAccount, QuestionButton, GitButton } from '../../atoms'
import { KnowledgeNavigation } from '../../molecules'

interface KnowledgeHeaderProps {
  className?: string
}

export const KnowledgeHeader = ({ className }: KnowledgeHeaderProps) => {
  return (
    <header className={`sticky top-0 z-50 backdrop-blur-sm bg-white/80 border-b border-gray-200 ${className || ''}`}>
      <div className="px-12 py-4">
        <Flex align="center" justify="between">
          <Logo />
          
          {/* Center Navigation */}
          <KnowledgeNavigation />
          
          {/* Right Side Actions */}
          <Flex align="center" gap="4">
            <LanguageSelector />
            <GitButton onClick={() => window.open('https://github.com', '_blank')} />
            <QuestionButton onClick={() => alert('Help center coming soon!')} />
            <ThemeToggle />
            <div className="w-px h-6 bg-gray-300 mx-2" />
            <UserAccount />
          </Flex>
        </Flex>
      </div>
    </header>
  )
}