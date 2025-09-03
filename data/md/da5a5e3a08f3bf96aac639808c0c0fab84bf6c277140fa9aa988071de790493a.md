# Sample Document for Testing

## Introduction

This is a sample Markdown document created specifically for testing the `/ingest-markdown` API endpoint in the Raptor Service.

## What is RAPTOR Technology?

RAPTOR (Recursive Abstractive Processing for Tree-Organized Retrieval) is an advanced document processing technology that:

- **Hierarchical Processing**: Organizes documents in tree structures for better retrieval
- **Abstractive Summarization**: Creates meaningful summaries at different levels
- **Intelligent Retrieval**: Enables more accurate and contextual search results

## Key Features

### Document Processing

- Automatic text chunking and segmentation
- Multi-level summarization
- Vector embedding generation
- Metadata extraction and indexing

### Search Capabilities

- Semantic search across document corpus
- Context-aware query rewriting
- Relevance scoring and ranking
- Multi-modal retrieval support

### AI Integration

- Support for multiple LLM providers (DeepSeek-V3, GPT-4o-mini, Gemini)
- Configurable temperature and token limits
- Streaming and non-streaming responses
- Custom model selection per query

## API Usage Examples

### Basic Upload

```bash
curl -X POST "http://localhost:8000/v1/documents/ingest-markdown" \
  -F "file=@document.md" \
  -F "dataset_id=my-dataset"
```

### Advanced Upload with Metadata

```bash
curl -X POST "http://localhost:8000/v1/documents/ingest-markdown" \
  -F "file=@document.md" \
  -F "dataset_id=my-dataset" \
  -F "source=API Documentation" \
  -F "tags=[\"documentation\", \"api\", \"guide\"]" \
  -F "build_tree=true" \
  -F "summary_llm=DeepSeek-V3"
```

## Best Practices

1. **File Format**: Always use `.md` extension for Markdown files
2. **Dataset ID**: Use descriptive, unique identifiers for datasets
3. **Metadata**: Include relevant tags and source information
4. **Tree Building**: Enable tree building for better hierarchical organization
5. **Model Selection**: Choose appropriate LLM based on your use case

## Troubleshooting

### Common Issues

- **File Format Error**: Ensure file has `.md` extension
- **Dataset Not Found**: Validate dataset ID before upload
- **Large Files**: Consider chunking very large documents
- **API Limits**: Respect rate limits and timeout settings

### Error Codes

- `400`: Bad Request - Invalid parameters or file format
- `404`: Dataset not found
- `413`: File too large
- `429`: Rate limit exceeded
- `500`: Internal server error

## Conclusion

This document serves as both a test file and documentation for the Raptor Service API. The hierarchical structure and diverse content types make it ideal for testing various aspects of the document processing pipeline.

For more information, visit the [API documentation](http://localhost:8000/docs) or contact the development team.

---

**Created**: $(date)
**Version**: 1.0
**Author**: API Test Suite
**Tags**: testing, documentation, raptor, api
