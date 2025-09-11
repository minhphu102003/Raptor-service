import React, { useState } from 'react';
import langfuse from '../services/langfuse';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
}

interface ChatWithLangfuseProps {
  sessionId: string;
}

const ChatWithLangfuse: React.FC<ChatWithLangfuseProps> = ({ sessionId }) => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);

  // Function to send a message to your backend
  const sendMessage = async (content: string) => {
    setLoading(true);
    try {
      // For LangfuseWeb v3, we'll use the traceId directly in scoring
      // and rely on backend tracing for the full trace
      const startTime = Date.now();
      
      // Call your backend API
      const response = await fetch('/api/v1/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          query: content,
          session_id: sessionId,
          // Add other parameters as needed
        }),
      });

      const data = await response.json();
      
      // Calculate duration
      const duration = Date.now() - startTime;
      
      // Send trace information to Langfuse after getting response
      // We can create a score or event to track this interaction
      try {
        await langfuse.score({
          traceId: sessionId,
          name: "chat-response-time",
          value: duration,
          comment: `Response time for chat message: ${duration}ms`
        });
      } catch (traceError) {
        console.warn('Failed to send trace data to Langfuse:', traceError);
      }
      
      // Add user message
      const userMessage: Message = {
        id: `msg-${Date.now()}-user`,
        role: 'user',
        content: content,
        timestamp: new Date(),
      };

      // Add assistant message
      const assistantMessage: Message = {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: data.answer,
        timestamp: new Date(),
      };

      setMessages(prev => [...prev, userMessage, assistantMessage]);
      setInput('');
    } catch (error) {
      console.error('Error sending message:', error);
    } finally {
      setLoading(false);
    }
  };

  // Function to send feedback to Langfuse
  const sendFeedback = async (messageId: string, feedback: 'positive' | 'negative', comment?: string) => {
    try {
      // Send feedback as a score to Langfuse
      await langfuse.score({
        traceId: sessionId, // Use session ID as trace ID
        observationId: messageId, // Use message ID as observation ID
        name: "user-feedback",
        value: feedback === 'positive' ? 1 : -1,
        comment: comment,
      });
      
      console.log(`Feedback sent for message ${messageId}: ${feedback}`);
    } catch (error) {
      console.error('Error sending feedback:', error);
    }
  };

  // Function to send detailed feedback with ratings
  const sendDetailedFeedback = async (
    messageId: string, 
    ratings: { relevance: number; accuracy: number; helpfulness: number },
    comment?: string
  ) => {
    try {
      // Send multiple scores for detailed feedback
      const scores = [
        { name: "relevance", value: ratings.relevance },
        { name: "accuracy", value: ratings.accuracy },
        { name: "helpfulness", value: ratings.helpfulness },
      ];

      for (const score of scores) {
        await langfuse.score({
          traceId: sessionId,
          observationId: messageId,
          name: `feedback_${score.name}`,
          value: score.value,
          comment: comment,
        });
      }
      
      console.log(`Detailed feedback sent for message ${messageId}`);
    } catch (error) {
      console.error('Error sending detailed feedback:', error);
    }
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !loading) {
      sendMessage(input.trim());
    }
  };

  return (
    <div className="chat-container">
      <div className="messages">
        {messages.map((message) => (
          <div key={message.id} className={`message ${message.role}`}>
            <div className="message-content">
              {message.content}
            </div>
            {message.role === 'assistant' && (
              <div className="feedback-buttons">
                <button 
                  onClick={() => sendFeedback(message.id, 'positive')}
                  className="feedback-btn positive"
                >
                  👍
                </button>
                <button 
                  onClick={() => sendFeedback(message.id, 'negative')}
                  className="feedback-btn negative"
                >
                  👎
                </button>
              </div>
            )}
            <div className="timestamp">
              {message.timestamp.toLocaleTimeString()}
            </div>
          </div>
        ))}
      </div>
      
      <form onSubmit={handleSubmit} className="input-form">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type your message..."
          disabled={loading}
          className="message-input"
        />
        <button 
          type="submit" 
          disabled={loading || !input.trim()}
          className="send-button"
        >
          {loading ? 'Sending...' : 'Send'}
        </button>
      </form>
    </div>
  );
};

export default ChatWithLangfuse;