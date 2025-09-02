# Document Upload Implementation Guide

This guide explains how to implement document upload functionality in the Raptor Service frontend application using the new custom hook and validation utilities.

## Overview

The document upload system consists of several components:

1. **Custom Hook**: `useDocumentUpload` - Handles API integration, validation, and state management
2. **Service Layer**: `DocumentService` - Makes actual API calls to the backend
3. **Validation Utilities**: `fileValidation.ts` - Provides frontend file validation
4. **UI Components**: Integration with existing UI components like AddDocumentModal

## Implementation Steps

### 1. Using the Custom Hook

The `useDocumentUpload` hook provides a complete solution for document uploading:

```typescript
import { useDocumentUpload } from "../hooks/useDocumentUpload";

// In your component
const {
  uploadDocuments,
  isUploading,
  uploadProgress,
  validateMarkdownFile,
  getFileSizeMB,
} = useDocumentUpload({
  datasetId: "your-dataset-uuid",
  onSuccess: (uploadedFiles) => {
    console.log("Upload successful:", uploadedFiles);
    // Refresh your document list here
  },
  onError: (error) => {
    console.error("Upload failed:", error);
    // Handle error display
  },
});
```

### 2. Preparing Upload Data

The hook expects an array of `UploadFileData` objects:

```typescript
interface UploadFileData {
  file: File;
  source?: string;
  tags?: string[];
  extraMeta?: string; // JSON string
  buildTree?: boolean;
  summaryLLM?: string;
  vectorIndex?: string; // JSON string
  upsertMode?: "upsert" | "replace" | "skip_duplicates";
}
```

### 3. Frontend Validation

Before uploading, validate files using the built-in validation:

```typescript
const fileData = { file: myFile };

// Validate the file
const validation = validateMarkdownFile(fileData.file);
if (!validation.isValid) {
  throw new Error(validation.error);
}

// Check for warnings
if (validation.warnings && validation.warnings.length > 0) {
  console.warn("File warnings:", validation.warnings);
}
```

### 4. Calling the Upload Function

```typescript
const handleUpload = async (files: File[]) => {
  const uploadData = files.map((file) => ({
    file,
    source: `Frontend upload: ${file.name}`,
    tags: ["frontend-upload"],
    extraMeta: JSON.stringify({
      originalFileName: file.name,
      uploadedBy: "frontend",
      timestamp: new Date().toISOString(),
    }),
    buildTree: true,
    summaryLLM: "DeepSeek-V3",
    upsertMode: "upsert",
  }));

  try {
    await uploadDocuments(uploadData);
    // Success handled by hook
  } catch (error) {
    // Error handled by hook
  }
};
```

## API Integration Details

### Endpoint

The API endpoint is: `POST /v1/documents/ingest-markdown`

### Required Parameters

1. `file` (FormData) - The Markdown file to upload
2. `dataset_id` (FormData) - The target dataset UUID

### Optional Parameters

1. `source` (FormData) - Source description
2. `tags` (FormData) - JSON array string of tags
3. `extra_meta` (FormData) - JSON string with additional metadata
4. `build_tree` (FormData) - Boolean string ("true"/"false")
5. `summary_llm` (FormData) - LLM model name
6. `vector_index` (FormData) - JSON string with vector index config
7. `upsert_mode` (FormData) - One of: "upsert", "replace", "skip_duplicates"

### Response Format

```json
{
  "document_id": "doc_abc123",
  "dataset_id": "dataset_xyz789",
  "status": "processed",
  "chunks_created": 15,
  "tree_built": true,
  "processing_time": 12.5,
  "dataset_info": {
    "name": "My Dataset",
    "document_count": 5
  }
}
```

## Validation Rules

### File Requirements

1. **Extension**: Must be `.md` or `.markdown`
2. **Size**: Maximum 10MB
3. **Content**: Must not be empty

### Error Handling

The hook provides comprehensive error handling:

- Frontend validation errors
- Network errors
- API response errors
- Partial upload failures

## UI Integration

### Progress Indication

The hook provides real-time upload progress:

```typescript
// uploadProgress is an object mapping filenames to progress percentages
{
  "document1.md": 75,
  "document2.md": 25
}
```

### Loading States

The `isUploading` boolean indicates when an upload is in progress.

## Testing

### Using Postman

1. Import the `Document_API_Tests.postman_collection.json` collection
2. Set environment variables:
   - `base_url`: Your API base URL (e.g., http://localhost:8000)
   - `dataset_id`: Your test dataset UUID
3. Run the "02 - Ingest Markdown (Full Parameters)" request
4. Select a Markdown file for upload

### Manual Testing

1. Create a test Markdown file
2. Navigate to the Dataset page
3. Click "Add Document"
4. Select your test file
5. Verify successful upload in the documents list

## Best Practices

1. **Always validate files** before attempting upload
2. **Provide user feedback** during upload process
3. **Handle errors gracefully** with clear messages
4. **Refresh document lists** after successful uploads
5. **Use appropriate LLM models** for summarization
6. **Respect file size limits** to prevent upload failures

## Troubleshooting

### Common Issues

1. **422 Validation Errors**: Check that all required form fields are properly set
2. **413 Payload Too Large**: Ensure file size is under 10MB
3. **400 Bad Request**: Verify JSON strings are properly formatted
4. **Network Errors**: Check API server is running and accessible

### Debugging Tips

1. Check browser console for detailed error messages
2. Verify API endpoint is correct in `DocumentService.ts`
3. Ensure dataset UUID exists in the backend
4. Check file validation rules match backend requirements
