# Postman API Testing Guide for Document Routes

## Overview

This guide provides step-by-step instructions for testing the Document API endpoints using Postman, specifically focusing on the `/ingest-markdown` endpoint that was recently optimized with consolidated form parameters.

## Setup Instructions

### 1. Import the Postman Collection

1. Open Postman
2. Click "Import" button
3. Select "File" tab
4. Choose the file: `postman_collections/Document_API_Tests.postman_collection.json`
5. Click "Import"

### 2. Configure Environment Variables

The collection uses variables that you can customize:

| Variable     | Default Value           | Description                    |
| ------------ | ----------------------- | ------------------------------ |
| `base_url`   | `http://localhost:8000` | API server base URL            |
| `dataset_id` | `test-dataset-123`      | Default dataset ID for testing |

To update these:

1. Click the collection name
2. Go to "Variables" tab
3. Update the values as needed

### 3. Prepare Test Files

Use the provided sample file at: `test_files/sample_document.md`
Or create your own Markdown file with `.md` extension.

## API Endpoints Testing

### 1. Validate Dataset (Optional but Recommended)

**Endpoint**: `POST /v1/documents/validate-dataset`

Test this first to ensure your dataset ID is valid:

1. Select "Validate Dataset" request
2. Verify the `dataset_id` parameter in the body
3. Click "Send"
4. Expected response: `{"valid": true, "message": "Dataset is ready for upload"}`

### 2. Ingest Markdown Document (Main Endpoint)

**Endpoint**: `POST /v1/documents/ingest-markdown`

#### Option A: Full Parameters Test

1. Select "Ingest Markdown Document" request
2. In the "Body" tab, ensure "form-data" is selected
3. Configure the file upload:
   - Click the file field dropdown next to "file"
   - Select "Select Files"
   - Choose your `.md` file (e.g., `test_files/sample_document.md`)
4. Review/modify form parameters:

| Parameter      | Example Value                                | Required | Description                       |
| -------------- | -------------------------------------------- | -------- | --------------------------------- |
| `file`         | `sample_document.md`                         | ✅       | Markdown file to upload           |
| `dataset_id`   | `test-dataset-123`                           | ✅       | Target dataset ID                 |
| `source`       | `API Test Upload`                            | ❌       | Source description                |
| `tags`         | `["test", "api", "documentation"]`           | ❌       | JSON array of tags                |
| `extra_meta`   | `{"author": "API Tester", "version": "1.0"}` | ❌       | Additional metadata as JSON       |
| `build_tree`   | `true`                                       | ❌       | Build RAPTOR tree (default: true) |
| `summary_llm`  | `DeepSeek-V3`                                | ❌       | LLM for summarization             |
| `vector_index` | `{"index_type": "faiss", "dimension": 1024}` | ❌       | Vector index config               |
| `upsert_mode`  | `upsert`                                     | ❌       | Duplicate handling mode           |

5. Optional: Add header `X-Dataset-Id` for alternative dataset specification
6. Click "Send"

#### Option B: Minimal Parameters Test

1. Select "Ingest Markdown - Minimal Parameters" request
2. Only configure:
   - `file`: Select your `.md` file
   - `dataset_id`: Your target dataset ID
3. Click "Send"

#### Expected Response Structure

```json
{
  "document_id": "doc_abc123",
  "dataset_id": "test-dataset-123",
  "status": "processed",
  "chunks_created": 15,
  "tree_built": true,
  "processing_time": 12.5,
  "dataset_info": {
    "name": "Test Dataset",
    "document_count": 1
  }
}
```

### 3. List Documents in Dataset

**Endpoint**: `GET /v1/documents/datasets/{dataset_id}/documents`

1. Select "List Documents in Dataset" request
2. The URL automatically uses the `{{dataset_id}}` variable
3. Modify query parameters if needed:
   - `page`: Page number (default: 1)
   - `page_size`: Documents per page (default: 20, max: 100)
4. Click "Send"

### 4. Retrieve Documents

**Endpoint**: `POST /v1/documents/retrieve`

1. Select "Retrieve Documents" request
2. Modify the JSON body with your query:

```json
{
  "query": "What is RAPTOR technology?",
  "dataset_ids": ["test-dataset-123"],
  "top_k": 5,
  "score_threshold": 0.7,
  "rewrite_query": true
}
```

3. Click "Send"

### 5. Answer Query

**Endpoint**: `POST /v1/documents/answer`

1. Select "Answer Query" request
2. Modify the JSON body:

```json
{
  "query": "What is RAPTOR technology and how does it work?",
  "dataset_ids": ["test-dataset-123"],
  "top_k": 5,
  "score_threshold": 0.7,
  "rewrite_query": true,
  "answer_model": "DeepSeek-V3",
  "temperature": 0.3,
  "max_tokens": 4000,
  "stream": false
}
```

3. Click "Send"

## Testing Scenarios

### Scenario 1: Happy Path

1. Validate dataset → Upload document → List documents → Retrieve → Answer query

### Scenario 2: Error Handling

- Test with invalid file format (non-.md file)
- Test with non-existent dataset ID
- Test with malformed JSON in metadata fields

### Scenario 3: Different LLM Models

Test with different `answer_model` values:

- `DeepSeek-V3`
- `GPT-4o-mini`
- `Gemini-2.5-Flash`
- `Claude-3.5-Haiku`

### Scenario 4: Different Upsert Modes

Test with different `upsert_mode` values:

- `upsert`: Update if exists, create if not
- `replace`: Replace existing document
- `skip_duplicates`: Skip if duplicate exists

## Troubleshooting

### Common Issues

1. **File Upload Issues**

   - Ensure file has `.md` extension
   - Check file size limits
   - Verify file is properly selected in Postman

2. **JSON Parameter Errors**

   - Validate JSON syntax for `tags`, `extra_meta`, `vector_index`
   - Use proper array format for tags: `["tag1", "tag2"]`
   - Use proper object format for metadata: `{"key": "value"}`

3. **Dataset Issues**

   - Run validate-dataset first
   - Ensure dataset exists and is accessible
   - Check dataset permissions

4. **Authentication Issues**
   - Verify API server is running
   - Check if authentication is required
   - Ensure proper headers are set

### Response Status Codes

| Code | Meaning           | Action                            |
| ---- | ----------------- | --------------------------------- |
| 200  | Success           | Request completed successfully    |
| 400  | Bad Request       | Check parameters and file format  |
| 401  | Unauthorized      | Check authentication              |
| 404  | Not Found         | Verify dataset ID and endpoints   |
| 413  | Payload Too Large | Reduce file size                  |
| 422  | Validation Error  | Check parameter types and formats |
| 429  | Rate Limit        | Wait and retry                    |
| 500  | Server Error      | Check server logs                 |

## Tips for Effective Testing

1. **Start Simple**: Begin with minimal parameters, then add complexity
2. **Use Variables**: Leverage Postman variables for consistent testing
3. **Save Responses**: Use Postman's response saving feature for documentation
4. **Test Edge Cases**: Try boundary values and error conditions
5. **Monitor Performance**: Check response times for large files
6. **Validate Results**: Verify that uploaded documents appear in listings

## Advanced Testing

### Pre-request Scripts

Add validation scripts before sending requests:

```javascript
// Validate file is selected
if (
  !pm.request.body.formdata.find((param) => param.key === "file" && param.src)
) {
  throw new Error("File must be selected for upload");
}
```

### Test Scripts

Add validation after receiving responses:

```javascript
// Validate successful upload
pm.test("Document uploaded successfully", function () {
  pm.response.to.have.status(200);
  pm.expect(pm.response.json()).to.have.property("document_id");
});
```

This guide should help you thoroughly test the optimized `/ingest-markdown` API endpoint and other document-related endpoints.
