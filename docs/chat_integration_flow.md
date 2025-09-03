# Chat Integration Flow

```mermaid
graph TD
    A[User] --> B[ChatPageTemplate]
    B --> C[useChatState Hook]
    C --> D[Chat Service]
    D --> E[Backend API]
    E --> F[Database]
    E --> G[Knowledge Base]
    D --> C
    C --> B
    B --> H[ChatArea Component]
    B --> I[ChartSection Component]
    B --> J[AssistantCreation Component]

    subgraph Frontend
        B
        C
        D
        H
        I
        J
    end

    subgraph Backend
        E
        F
        G
    end

    H --> A
    I --> A
    J --> A
```

## Component Interaction Flow

1. **User Interaction**

   - User selects an assistant in AssistantCreation
   - User selects or creates a session in ChartSection
   - User sends messages in ChatArea

2. **State Management**

   - useChatState manages all chat-related state
   - Automatically loads sessions when assistant changes
   - Automatically loads messages when session changes

3. **API Communication**

   - ChatService handles all API calls
   - Provides methods for session management
   - Provides methods for message handling
   - Provides methods for context-aware responses

4. **Data Flow**
   - Assistant selection → Load sessions
   - Session selection → Load messages
   - Message sending → API call → Update UI
   - Context retrieval → Enhanced responses

## Key Implementation Details

### Session Management

```mermaid
sequenceDiagram
    participant U as User
    participant CA as ChatArea
    participant CS as ChatState
    participant SVC as ChatService
    participant API as Backend API

    U->>CA: Select Assistant
    CA->>CS: selectAssistant()
    CS->>SVC: listSessions()
    SVC->>API: GET /sessions
    API-->>SVC: Session List
    SVC-->>CS: Session List
    CS->>CA: Update sessions state

    U->>CA: Select Session
    CA->>CS: selectSession()
    CS->>SVC: getMessages()
    SVC->>API: GET /sessions/{id}/messages
    API-->>SVC: Message List
    SVC-->>CS: Message List
    CS->>CA: Update messages state
```

### Message Sending

```mermaid
sequenceDiagram
    participant U as User
    participant CA as ChatArea
    participant CS as ChatState
    participant SVC as ChatService
    participant API as Backend API

    U->>CA: Send Message
    CA->>CS: sendMessageToAssistant()
    CS->>SVC: sendMessage()
    SVC->>API: POST /chat
    API-->>SVC: Response
    SVC-->>CS: Response
    CS->>CA: Update messages state
```

### Enhanced Message Sending

```mermaid
sequenceDiagram
    participant U as User
    participant CA as ChatArea
    participant CS as ChatState
    participant SVC as ChatService
    participant API as Backend API

    U->>CA: Send Message with Files
    CA->>CS: sendEnhancedMessageToAssistant()
    CS->>SVC: sendEnhancedMessage()
    SVC->>API: POST /chat/enhanced
    API-->>SVC: Response
    SVC-->>CS: Response
    CS->>CA: Update messages state
```

This flow ensures a smooth, context-aware chat experience with proper state management and API integration.
