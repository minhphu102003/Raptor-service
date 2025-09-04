import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { motion } from 'framer-motion';
// Typing effect is now handled in the ChatMessage component, so we don't need to import it here

interface MessageContentProps {
  content: string;
  isUser: boolean;
}

export const MessageContent = ({ content, isUser }: MessageContentProps) => {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ duration: 0.5 }}
    >
      <div 
        className={`text-sm ${
          isUser ? 'text-white' : 'text-gray-900'
        } prose prose-sm max-w-none`}
      >
        <ReactMarkdown
          remarkPlugins={[remarkGfm]}
          components={{
            p: ({ ...props }) => <p className="mb-3 last:mb-0" {...props} />,
            ul: ({ ...props }) => <ul className="list-disc list-inside mb-3" {...props} />,
            ol: ({ ...props }) => <ol className="list-decimal list-inside mb-3" {...props} />,
            li: ({ ...props }) => <li className="mb-1" {...props} />,
            a: ({ ...props }) => <a className="text-blue-500 hover:underline" target="_blank" rel="noopener noreferrer" {...props} />,
            code: ({ ...props }) => 
              <code 
                className="bg-gray-200 dark:bg-gray-700 rounded px-1 py-0.5 text-sm font-mono" 
                {...props} 
              />,
            pre: ({ ...props }) => 
              <pre 
                className="bg-gray-100 dark:bg-gray-800 rounded p-3 overflow-x-auto text-sm" 
                {...props} 
              />,
            blockquote: ({ ...props }) => 
              <blockquote 
                className="border-l-4 border-gray-300 pl-4 italic text-gray-600" 
                {...props} 
              />,
            h1: ({ ...props }) => <h1 className="text-2xl font-bold mt-4 mb-2" {...props} />,
            h2: ({ ...props }) => <h2 className="text-xl font-bold mt-3 mb-2" {...props} />,
            h3: ({ ...props }) => <h3 className="text-lg font-bold mt-2 mb-1" {...props} />,
            h4: ({ ...props }) => <h4 className="text-base font-bold mt-2 mb-1" {...props} />,
            h5: ({ ...props }) => <h5 className="text-sm font-bold mt-1 mb-1" {...props} />,
            h6: ({ ...props }) => <h6 className="text-xs font-bold mt-1 mb-1" {...props} />,
            table: ({ ...props }) => <table className="min-w-full border-collapse border border-gray-300 my-2" {...props} />,
            th: ({ ...props }) => <th className="border border-gray-300 px-3 py-1 bg-gray-100 font-bold" {...props} />,
            td: ({ ...props }) => <td className="border border-gray-300 px-3 py-1" {...props} />,
            tr: ({ ...props }) => <tr {...props} />
          }}
        >
          {content}
        </ReactMarkdown>
      </div>
    </motion.div>
  );
};