import { Flex } from '@radix-ui/themes'

export const ChatSessionSkeleton = () => {
  return (
    <div className="p-3 rounded-lg border border-gray-200 bg-white animate-pulse">
      <div className="h-4 bg-gray-200 rounded w-3/4 mb-2"></div>
      <Flex align="center" justify="between" className="mb-1">
        <div className="h-3 bg-gray-200 rounded w-1/3"></div>
        <Flex align="center" gap="1">
          <div className="h-3 bg-gray-200 rounded w-16"></div>
        </Flex>
      </Flex>
      <div className="h-3 bg-gray-200 rounded w-1/2"></div>
    </div>
  )
}