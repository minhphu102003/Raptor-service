# Knowledge Base Management API Documentation

This document describes the API endpoints for managing knowledge bases (datasets) in the RAPTOR service.

## Overview

The knowledge base management system provides endpoints to:

- List all available knowledge bases
- Get detailed information about specific knowledge bases
- View documents within knowledge bases
- Validate knowledge base IDs for upload
- Delete knowledge bases and their data
- Upload documents to knowledge bases

## Base URL

All endpoints are prefixed with `/v1/`

## Authentication

Currently uses placeholder authentication. All endpoints require the `auth_dep()` dependency.

---

## Dataset/Knowledge Base Endpoints

### 1. List All Knowledge Bases

**GET** `/v1/datasets/`

List all available knowledge bases with their metadata.

**Response:**

```json
{
  "datasets": [
    {
      "id": "customer-support",
      "name": "customer-support",
      "title": "customer-support",
      "description": "Knowledge base with 15 documents",
      "document_count": 15,
      "created_at": "2024-01-15T10:30:00Z",
      "last_updated": "2024-01-20T14:22:00Z"
    }
  ],
  "total": 1
}
```

### 2. Get Knowledge Base Details

**GET** `/v1/datasets/{dataset_id}`

Get detailed information about a specific knowledge base.

**Parameters:**

- `dataset_id` (path): The unique identifier of the knowledge base

**Response:**

```json
{
  "id": "customer-support",
  "name": "customer-support",
  "description": "Knowledge base containing 15 documents",
  "document_count": 15,
  "chunk_count": 234,
  "embedding_count": 234,
  "tree_count": 2,
  "created_at": "2024-01-15T10:30:00Z",
  "last_updated": "2024-01-20T14:22:00Z",
  "status": "active",
  "total_tokens": 45678,
  "embedding_models": ["voyage-context-3"],
  "processing_status": "completed",
  "has_embeddings": true,
  "has_trees": true,
  "avg_tokens_per_chunk": 195.2,
  "avg_chunks_per_document": 15.6
}
```

**Error Responses:**

- `404 Not Found`: Knowledge base not found
- `400 Bad Request`: Invalid dataset ID

### 3. List Documents in Knowledge Base

**GET** `/v1/datasets/{dataset_id}/documents`

Get a paginated list of documents in a specific knowledge base.

**Parameters:**

- `dataset_id` (path): The unique identifier of the knowledge base
- `page` (query, optional): Page number, starts from 1 (default: 1)
- `page_size` (query, optional): Number of documents per page, max 100 (default: 20)

**Response:**

```json
{
  "documents": [
    {
      "doc_id": "doc_123",
      "source": "file:///path/to/document.md",
      "tags": ["support", "faq"],
      "extra_meta": { "category": "billing" },
      "checksum": "sha256hash...",
      "created_at": "2024-01-15T10:30:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "page_size": 20,
    "total": 15,
    "pages": 1
  }
}
```

### 4. Get Knowledge Base Statistics

**GET** `/v1/datasets/{dataset_id}/statistics`

Get comprehensive statistics for a knowledge base.

**Response:**

```json
{
  "dataset_id": "customer-support",
  "document_count": 15,
  "chunk_count": 234,
  "embedding_count": 234,
  "tree_count": 2,
  "total_tokens": 45678,
  "embedding_models": ["voyage-context-3"],
  "processing_status": "completed",
  "has_embeddings": true,
  "has_trees": true,
  "avg_tokens_per_chunk": 195.2,
  "avg_chunks_per_document": 15.6,
  "created_at": "2024-01-15T10:30:00Z",
  "last_updated": "2024-01-20T14:22:00Z"
}
```

### 5. Validate Knowledge Base ID

**POST** `/v1/datasets/{dataset_id}/validate`

Validate if a knowledge base ID is valid and ready for document upload.

**Response:**

```json
{
  "dataset_id": "new-knowledge-base",
  "exists": false,
  "valid": true,
  "ready_for_upload": true,
  "message": "Dataset new-knowledge-base is ready for document upload"
}
```

**Validation Rules:**

- Must be at least 2 characters long
- Cannot exceed 64 characters
- Can only contain letters, numbers, hyphens, and underscores
- Must match pattern: `^[a-zA-Z0-9_-]+$`

### 6. Check Knowledge Base Existence

**HEAD** `/v1/datasets/{dataset_id}`

Check if a knowledge base exists (returns HTTP status only).

**Response:**

- `200 OK`: Knowledge base exists
- `404 Not Found`: Knowledge base does not exist

### 7. Delete Knowledge Base

**DELETE** `/v1/datasets/{dataset_id}`

Delete a knowledge base and all its associated data.

**⚠️ Warning:** This operation cannot be undone!

**Response:**

```json
{
  "message": "Dataset 'customer-support' deleted successfully",
  "details": {
    "dataset_id": "customer-support",
    "deleted_at": "2024-01-20T15:30:00Z",
    "deletion_stats": {
      "documents_deleted": 15,
      "embeddings_deleted": 234,
      "trees_deleted": 2
    },
    "original_info": {
      "document_count": 15,
      "chunk_count": 234
    }
  }
}
```

---

## Document Management Endpoints

### 8. Upload Document to Knowledge Base

**POST** `/v1/documents/ingest-markdown`

Upload a Markdown document to a specified knowledge base.

**Parameters:**

- `file` (form-data): The Markdown file to upload (.md extension required)
- `dataset_id` (form-data): The target knowledge base ID
- `source` (form-data, optional): Source description
- `tags` (form-data, optional): List of tags for categorization
- `extra_meta` (form-data, optional): Additional metadata as JSON string
- `build_tree` (form-data, optional): Whether to build RAPTOR tree (default: true)
- `summary_llm` (form-data, optional): LLM model for summarization
- `vector_index` (form-data, optional): Vector index configuration as JSON
- `upsert_mode` (form-data, optional): Handle duplicates: "upsert", "replace", "skip_duplicates"
- `X-Dataset-Id` (header, optional): Alternative way to specify dataset ID

**Response:**

```json
{
  "doc_id": "doc_456",
  "dataset_id": "customer-support",
  "status": "processing",
  "message": "Document uploaded successfully",
  "dataset_info": {
    "name": "customer-support",
    "document_count": 16
  }
}
```

### 9. List Documents by Knowledge Base (Alternative Endpoint)

**GET** `/v1/documents/datasets/{dataset_id}/documents`

Alternative endpoint for listing documents in a knowledge base (same as `/v1/datasets/{dataset_id}/documents`).

### 10. Validate Knowledge Base for Upload

**POST** `/v1/documents/validate-dataset`

Validate a knowledge base ID before uploading (form-data version).

**Parameters:**

- `dataset_id` (form-data): The knowledge base ID to validate

---

## Query and Retrieval Endpoints

### 11. Retrieve Information

**POST** `/v1/documents/retrieve`

Retrieve relevant information from a knowledge base using semantic search.

**Request Body:**

```json
{
  "dataset_id": "customer-support",
  "query": "How do I cancel my subscription?",
  "mode": "collapsed",
  "top_k": 8,
  "expand_k": 5,
  "levels_cap": 0,
  "use_reranker": false,
  "reranker_model": null,
  "byok_voyage_api_key": null
}
```

**Parameters:**

- `dataset_id`: Knowledge base to search in
- `query`: Natural language query
- `mode`: "collapsed" or "traversal" search mode
- `top_k`: Number of results to return (default: 8)
- `expand_k`: Expansion factor for hierarchical search (default: 5)
- `levels_cap`: Maximum tree levels to search (default: 0 = no limit)
- `use_reranker`: Whether to use reranking (default: false)
- `reranker_model`: Reranker model to use
- `byok_voyage_api_key`: Bring your own Voyage AI API key

### 12. Generate Answer

**POST** `/v1/documents/answer`

Generate an AI-powered answer based on retrieved information.

**Request Body:**

```json
{
  "dataset_id": "customer-support",
  "query": "How do I cancel my subscription?",
  "mode": "collapsed",
  "top_k": 8,
  "answer_model": "DeepSeek-V3",
  "temperature": 0.3,
  "max_tokens": 4000,
  "stream": false
}
```

**Additional Parameters:**

- `answer_model`: "DeepSeek-V3", "GPT-4o-mini", "Gemini-2.5-Flash", "Claude-3.5-Haiku"
- `temperature`: Response randomness (0.0-1.0)
- `max_tokens`: Maximum response length
- `stream`: Whether to stream the response

---

## Error Handling

### Common Error Responses

**400 Bad Request**

```json
{
  "detail": "Dataset ID cannot be empty"
}
```

**404 Not Found**

```json
{
  "detail": "Dataset 'non-existent-kb' not found"
}
```

**500 Internal Server Error**

```json
{
  "detail": "Failed to retrieve datasets"
}
```

### Error Codes

The service uses structured error handling with specific error codes:

- `DATASET_LIST_FAILED`: Failed to list datasets
- `DATASET_DETAILS_FAILED`: Failed to get dataset details
- `DATASET_DOCUMENTS_FAILED`: Failed to get dataset documents
- `DATASET_DELETE_FAILED`: Failed to delete dataset
- `DATASET_STATS_FAILED`: Failed to get dataset statistics
- `DATASET_VALIDATION_FAILED`: Failed to validate dataset

---

## Usage Examples

### Frontend Integration

```typescript
// List all knowledge bases
const response = await fetch("/v1/datasets/");
const { datasets } = await response.json();

// Upload document to knowledge base
const formData = new FormData();
formData.append("file", markdownFile);
formData.append("dataset_id", "customer-support");
formData.append("build_tree", "true");

const uploadResponse = await fetch("/v1/documents/ingest-markdown", {
  method: "POST",
  body: formData,
});

// Search in knowledge base
const searchResponse = await fetch("/v1/documents/retrieve", {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    dataset_id: "customer-support",
    query: "How to cancel subscription?",
    top_k: 5,
  }),
});
```

### Knowledge Base Workflow

1. **List existing knowledge bases** - `GET /v1/datasets/`
2. **Validate new knowledge base ID** - `POST /v1/datasets/{id}/validate`
3. **Upload documents** - `POST /v1/documents/ingest-markdown`
4. **Check processing status** - `GET /v1/datasets/{id}/statistics`
5. **Query knowledge base** - `POST /v1/documents/retrieve`
6. **Generate answers** - `POST /v1/documents/answer`

---

## Implementation Notes

### Database Design

The system uses the existing `dataset_id` field in documents as the knowledge base identifier. No separate knowledge base table is created, instead:

- Knowledge bases are identified by unique `dataset_id` values
- Metadata is aggregated from related tables (documents, chunks, embeddings, trees)
- Statistics are computed on-demand from the existing data

### Performance Considerations

- Pagination is implemented for document listings
- Statistics queries are optimized with proper indexes
- Large dataset operations may take time and should be used carefully

### Backwards Compatibility

All existing endpoints remain functional. New endpoints are additive and don't break existing functionality.
