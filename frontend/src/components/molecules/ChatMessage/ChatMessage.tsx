import { Avatar } from '@heroui/react';
import { Text } from '@radix-ui/themes';
import { motion } from 'framer-motion';
import { TypingIndicator } from '../../atoms/TypingIndicator';
import { MessageContent } from '../../atoms/MessageContent';

interface ChatMessageProps {
  message: {
    id: string;
    type: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    contextPassages?: Array<{
      content?: string;
    }>;
  };
}

export const ChatMessage = ({ message }: ChatMessageProps) => {
  const isUser = message.type === 'user';

  return (
    <motion.div
      key={message.id}
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      exit={{ opacity: 0 }}
      transition={{ duration: 0.3 }}
      className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'}`}
    >
      {!isUser && (
        <Avatar
          size="sm"
          className="bg-indigo-600 text-white flex-shrink-0"
          fallback="AI"
        />
      )}

      <div
        className={`max-w-[80%] p-4 rounded-lg ${
          isUser
            ? 'bg-indigo-600 text-white'
            : 'bg-gray-100 text-gray-900'
        }`}
      >
        {message.content === 'typing' ? (
          <TypingIndicator />
        ) : (
          <>
            <MessageContent content={message.content} isUser={isUser} />
            
            {message.contextPassages && message.contextPassages.length > 0 && (
              <div className="mt-2 pt-2 border-t border-gray-200">
                <Text className="text-xs text-gray-500">Context passages:</Text>
                <ul className="mt-1 space-y-1">
                  {message.contextPassages.slice(0, 3).map((passage, index) => (
                    <li key={index} className="text-xs text-gray-600 truncate">
                      • {passage.content && typeof passage.content === 'string' ? passage.content.substring(0, 100) : '...'}...
                    </li>
                  ))}
                </ul>
              </div>
            )}
            
            <Text className={`text-xs mt-2 ${isUser ? 'text-indigo-200' : 'text-gray-500'}`}>
              {message.timestamp.toLocaleTimeString()}
            </Text>
          </>
        )}
      </div>

      {isUser && (
        <Avatar
          size="sm"
          className="bg-gray-600 text-white flex-shrink-0"
          fallback="U"
        />
      )}
    </motion.div>
  );
};