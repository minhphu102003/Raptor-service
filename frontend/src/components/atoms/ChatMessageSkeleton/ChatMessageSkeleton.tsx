import { memo } from 'react';

export const ChatMessageSkeleton = memo(({ isUser = false }: { isUser?: boolean }) => {
  // Generate random widths for skeleton lines to make it more natural
  const getWidthClass = (index: number) => {
    if (isUser) {
      // User messages (right aligned) - shorter lines
      const widths = ['w-3/4', 'w-4/5', 'w-5/6', 'w-2/3'];
      return widths[index % widths.length];
    } else {
      // Assistant messages (left aligned) - varying lengths
      const widths = ['w-4/5', 'w-5/6', 'w-3/4', 'w-2/3'];
      return widths[index % widths.length];
    }
  };

  return (
    <div className={`flex gap-3 ${isUser ? 'justify-end' : 'justify-start'} mb-4`}>
      {!isUser && (
        <div className="w-8 h-8 rounded-full bg-gray-300 animate-pulse flex-shrink-0"></div>
      )}
      
      <div className={`max-w-[80%] rounded-lg p-4 ${isUser ? 'bg-indigo-600' : 'bg-gray-100'}`}>
        <div className="space-y-2">
          <div className={`h-4 ${isUser ? 'bg-indigo-400' : 'bg-gray-300'} rounded animate-pulse`}></div>
          <div className={`h-4 ${isUser ? 'bg-indigo-400' : 'bg-gray-300'} rounded animate-pulse ${getWidthClass(1)}`}></div>
          <div className={`h-4 ${isUser ? 'bg-indigo-400' : 'bg-gray-300'} rounded animate-pulse ${getWidthClass(2)}`}></div>
        </div>
        
        {/* Time skeleton */}
        <div className={`h-3 mt-2 w-16 ${isUser ? 'bg-indigo-400' : 'bg-gray-300'} rounded animate-pulse`}></div>
      </div>
      
      {isUser && (
        <div className="w-8 h-8 rounded-full bg-gray-300 animate-pulse flex-shrink-0"></div>
      )}
    </div>
  );
});

// Add display name for debugging
ChatMessageSkeleton.displayName = 'ChatMessageSkeleton';