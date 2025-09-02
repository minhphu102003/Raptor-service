# Debugging Document Upload Issues

This guide will help you debug the 400 error you're encountering when uploading documents from the frontend.

## Frontend Debugging

With the logging we've added, you should see detailed information in your browser's developer console:

1. Open your browser's Developer Tools (F12)
2. Go to the Console tab
3. Try to upload a document
4. Look for log messages starting with:
   - `[DocumentService]`
   - `[useDocumentUpload]`
   - `[DatasetPage]`

These logs will show you exactly what data is being sent to the backend.

## Backend Debugging

The backend will now log detailed information about what it receives:

1. Check your FastAPI server logs
2. Look for log messages starting with:
   - `INFO:__main__:Received ingest-markdown request`
   - `INFO:__main__:IngestMarkdownForm.as_form called with:`

## Common Issues and Solutions

### 1. Missing Required Fields

Check that all required fields are being sent:

- `file` (the actual file)
- `dataset_id` (the target dataset UUID)

### 2. Incorrect Data Types

Ensure form fields are being sent with the correct data types:

- `build_tree` should be "true" or "false" (string)
- `tags` should be a JSON array string
- `extra_meta` should be a JSON object string

### 3. File Validation Issues

Make sure your file:

- Has a .md or .markdown extension
- Is not larger than 10MB
- Is not empty

## How to Interpret the Logs

### Frontend Logs

```
[DocumentService] Upload request data: {
  file: "test.md",
  fileSize: 1024,
  fileType: "",
  datasetId: "dataset-123",
  source: "Frontend upload: test.md",
  tags: ["frontend-upload", "user-content"],
  extraMeta: "{\"originalFileName\":\"test.md\",...}",
  buildTree: true,
  summaryLLM: "DeepSeek-V3",
  vectorIndex: undefined,
  upsertMode: "upsert"
}
```

### Backend Logs

```
INFO:__main__:Received ingest-markdown request
INFO:__main__:File: test.md
INFO:__main__:Form data: dataset_id='dataset-123' source='Frontend upload: test.md' ...
INFO:__main__:IngestMarkdownForm.as_form called with:
INFO:__main__:  dataset_id: dataset-123
INFO:__main__:  source: Frontend upload: test.md
INFO:__main__:  tags: ["frontend-upload", "user-content"]
INFO:__main__:  extra_meta: {"originalFileName": "test.md", ...}
INFO:__main__:  build_tree: True
INFO:__main__:  summary_llm: DeepSeek-V3
INFO:__main__:  upsert_mode: upsert
```

## Testing with Postman

To compare with a working request, test with Postman:

1. Import the `Document_API_Tests.postman_collection.json`
2. Run the "02 - Ingest Markdown (Full Parameters) - FIXED" request
3. Compare the logs from this working request with your frontend logs

## Troubleshooting Steps

1. **Check the Network Tab**

   - Open Developer Tools → Network tab
   - Filter by XHR/Fetch
   - Upload a document
   - Look at the failed request
   - Check the Request Headers, Form Data, and Response

2. **Compare Frontend vs Postman**

   - Look at what Postman sends (working case)
   - Compare with what your frontend sends (failing case)
   - Identify any differences

3. **Check the Response**

   - Look at the full error response from the server
   - It may contain specific details about what's wrong

4. **Validate Your Dataset ID**
   - Make sure the dataset ID exists in your backend
   - Test with the validate-dataset endpoint first

## Removing Debug Logging

Once you've fixed the issue, you can remove the debug logging by:

1. Removing the console.log statements from:

   - `frontend/src/services/DocumentService.ts`
   - `frontend/src/hooks/useDocumentUpload.ts`
   - `frontend/src/pages/DatasetPage.tsx`

2. Removing the logger statements from:
   - `routes/document_routes.py`

This will clean up the logs for production use.
