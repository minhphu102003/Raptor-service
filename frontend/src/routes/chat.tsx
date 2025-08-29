import { createFileRoute } from '@tanstack/react-router'
import { ChatPage } from '../pages'

export const Route = createFileRoute('/chat')({
  component: () => <ChatPage />
})
