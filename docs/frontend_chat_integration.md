# Frontend Chat Integration Guide

This document explains how to integrate the new chat functionality with context-aware responses in the frontend application.

## Overview

The implementation provides a complete chat experience with:

- Session management
- Context-aware messaging
- Enhanced messaging with file attachments
- Real-time message display
- Loading states and error handling

## Key Components

### 1. Chat Service (`chatService.ts`)

The chat service provides all API calls needed for chat functionality:

```typescript
// Create a new chat session
const session = await chatService.createSession({
  dataset_id: "dataset-123",
  title: "My Chat Session",
  assistant_id: "assistant-456",
});

// Send a message
const response = await chatService.sendMessage({
  query: "What is machine learning?",
  dataset_id: "dataset-123",
  session_id: "session-789",
});

// Send an enhanced message with context
const enhancedResponse = await chatService.sendEnhancedMessage({
  query: "Explain neural networks",
  dataset_id: "dataset-123",
  session_id: "session-789",
  use_enhanced_context: true,
  additional_context: { uploadedFiles: "document.pdf" },
});

// Get session messages
const messages = await chatService.getMessages("session-789");

// Get session context
const context = await chatService.getSessionContext("session-789");
```

### 2. Chat State Hook (`useChatState.ts`)

The `useChatState` hook manages all chat-related state and provides functions for chat operations:

```typescript
const {
  // State
  selectedAssistant,
  selectedSession,
  sessions,
  messages,
  loadingSessions,
  loadingMessages,

  // Actions
  selectAssistant,
  createNewSession,
  selectSession,
  sendMessageToAssistant,
  sendEnhancedMessageToAssistant,
} = useChatState();
```

### 3. Chat Components

#### ChatArea

Displays messages and provides input functionality:

```tsx
<ChatArea
  selectedSession={selectedSession}
  messages={messages}
  onSendMessage={handleSendMessage}
  isSendingMessage={isSendingMessage}
/>
```

#### ChartSection

Displays session list and statistics:

```tsx
<ChartSection
  selectedAssistant={selectedAssistant}
  sessions={sessions}
  selectedSession={selectedSession}
  loadingSessions={loadingSessions}
  onSelectSession={handleSelectSession}
  onCreateNewSession={handleCreateNewSession}
/>
```

## Implementation Details

### Message Flow

1. User selects an assistant
2. Sessions for that assistant are loaded automatically
3. User selects a session or creates a new one
4. Messages for the session are loaded
5. User sends a message:
   - If files are attached, uses enhanced messaging
   - Otherwise uses regular messaging
6. Response is received and displayed

### Context-Aware Responses

The system automatically:

- Maintains conversation history
- Retrieves relevant context from knowledge bases
- Builds enhanced prompts with context
- Generates responses based on both history and context

### Error Handling

All API calls include proper error handling:

- Network errors are caught and displayed
- User-friendly error messages are shown
- Failed messages are logged to console

## Usage Examples

### Sending a Regular Message

```typescript
const handleSendMessage = async (content: string) => {
  if (!selectedSession || !selectedAssistant) return;

  try {
    await sendMessageToAssistant(
      content,
      selectedSession.id,
      selectedAssistant.knowledgeBases[0]
    );
  } catch (error) {
    console.error("Failed to send message:", error);
    addMessage({
      type: "assistant",
      content: "Sorry, I encountered an error processing your request.",
      timestamp: new Date(),
      sessionId: selectedSession.id,
    });
  }
};
```

### Sending an Enhanced Message with Files

```typescript
const handleSendMessageWithFiles = async (
  content: string,
  files: FileUploadItem[]
) => {
  if (!selectedSession || !selectedAssistant) return;

  try {
    const fileNames = files.map((f) => f.name).join(", ");
    const additionalContext = {
      uploadedFiles: fileNames,
    };

    await sendEnhancedMessageToAssistant(
      content,
      selectedSession.id,
      selectedAssistant.knowledgeBases[0],
      additionalContext
    );
  } catch (error) {
    console.error("Failed to send enhanced message:", error);
  }
};
```

### Loading Messages for a Session

Messages are automatically loaded when a session is selected through the `useEffect` hook in `useChatState`:

```typescript
useEffect(() => {
  const loadMessages = async () => {
    if (selectedSession) {
      setLoadingMessages(true);
      try {
        const apiMessages = await chatService.getMessages(selectedSession.id);
        const convertedMessages: Message[] = apiMessages.map((msg) => ({
          id: msg.message_id,
          sessionId: msg.session_id,
          type: msg.role,
          content: msg.content,
          timestamp: new Date(msg.created_at),
          contextPassages: msg.context_passages,
        }));
        setMessages(convertedMessages);
      } catch (error) {
        console.error("Failed to load messages:", error);
        setMessages([]);
      } finally {
        setLoadingMessages(false);
      }
    } else {
      setMessages([]);
    }
  };

  loadMessages();
}, [selectedSession]);
```

## Best Practices

1. **Always check for selected session and assistant** before sending messages
2. **Handle loading states** to provide visual feedback to users
3. **Implement proper error handling** for all API calls
4. **Use enhanced messaging** when context or file information is important
5. **Update session information** when messages are sent or received
6. **Scroll to bottom** when new messages are added for better UX

## API Endpoints Used

- `POST /datasets/chat/sessions` - Create session
- `GET /datasets/chat/sessions` - List sessions
- `GET /datasets/chat/sessions/{session_id}/messages` - Get messages
- `POST /datasets/chat/chat` - Send message
- `POST /datasets/chat/chat/enhanced` - Send enhanced message
- `PUT /datasets/chat/sessions/{session_id}` - Update session
- `GET /datasets/chat/sessions/{session_id}/context` - Get session context

This implementation provides a robust foundation for context-aware chat interactions that leverage both conversation history and knowledge base information.
