import { apiRequest } from './api'
import { KnowledgeBaseService } from './knowledgeBaseService'

export interface UploadDocumentData {
  file: File
  datasetId: string
  source?: string
  tags?: string[]
  extraMeta?: string // JSON string instead of object
  buildTree?: boolean
  summaryLLM?: string // Match the API field name
  vectorIndex?: string // JSON string instead of object
  upsertMode?: 'upsert' | 'replace' | 'skip_duplicates'
}

export interface DocumentUploadResponse {
  document_id: string
  dataset_id: string
  status: string
  chunks_created?: number
  tree_built?: boolean
  processing_time?: number
  dataset_info?: {
    name: string
    document_count: number
  }
}

export class DocumentService {
  // Upload a document to a knowledge base (using UUID as dataset_id)
  static async uploadDocument(data: UploadDocumentData): Promise<DocumentUploadResponse> {
    // Verify the knowledge base exists in localStorage
    if (!KnowledgeBaseService.exists(data.datasetId)) {
      throw new Error(`Knowledge base with ID "${data.datasetId}" not found`)
    }

    // Prepare form data according to the fixed API specification
    const formData = new FormData()
    formData.append('file', data.file)
    formData.append('dataset_id', data.datasetId)
    
    if (data.source) {
      formData.append('source', data.source)
    }
    
    if (data.tags && data.tags.length > 0) {
      // Send tags as JSON array string
      formData.append('tags', JSON.stringify(data.tags))
    }
    
    if (data.extraMeta) {
      formData.append('extra_meta', data.extraMeta)
    }
    
    if (data.buildTree !== undefined) {
      formData.append('build_tree', data.buildTree.toString())
    }
    
    if (data.summaryLLM) {
      formData.append('summary_llm', data.summaryLLM)
    }
    
    if (data.vectorIndex) {
      formData.append('vector_index', data.vectorIndex)
    }
    
    if (data.upsertMode) {
      formData.append('upsert_mode', data.upsertMode)
    }

    // Debug: Log form data before sending
    console.log('[DocumentService] Upload request data:', {
      file: data.file.name,
      fileSize: data.file.size,
      fileType: data.file.type,
      datasetId: data.datasetId,
      source: data.source,
      tags: data.tags,
      extraMeta: data.extraMeta,
      buildTree: data.buildTree,
      summaryLLM: data.summaryLLM,
      vectorIndex: data.vectorIndex,
      upsertMode: data.upsertMode
    })

    // Debug: Log FormData entries
    console.log('[DocumentService] FormData entries:')
    for (const [key, value] of formData.entries()) {
      if (value instanceof File) {
        console.log(`  ${key}: File { name: ${value.name}, size: ${value.size}, type: ${value.type} }`)
      } else {
        console.log(`  ${key}: ${value}`)
      }
    }

    try {
      // Call the upload API with the exact endpoint from Postman collection
      const response = await fetch(`http://localhost:8000/v1/documents/ingest-markdown`, {
        method: 'POST',
        body: formData,
      })

      console.log('[DocumentService] Upload response:', {
        status: response.status,
        statusText: response.statusText
      })

      if (!response.ok) {
        let errorMessage: string
        try {
          const errorData = await response.json()
          errorMessage = errorData.detail || errorData.message || `HTTP ${response.status}: ${response.statusText}`
          console.error('[DocumentService] Upload error details:', errorData)
        } catch {
          errorMessage = `HTTP ${response.status}: ${response.statusText}`
          const errorText = await response.text()
          console.error('[DocumentService] Upload error text:', errorText)
        }
        throw new Error(`Upload failed: ${errorMessage}`)
      }

      const result: DocumentUploadResponse = await response.json()
      console.log('[DocumentService] Upload success result:', result)

      // Update document count in localStorage
      KnowledgeBaseService.incrementDocumentCount(data.datasetId)

      return result
    } catch (error) {
      console.error('[DocumentService] Document upload failed:', error)
      throw error
    }
  }

  // Get documents for a knowledge base (this would call your existing API)
  static async getDocuments(datasetId: string, page: number = 1, pageSize: number = 20) {
    // Verify the knowledge base exists in localStorage
    if (!KnowledgeBaseService.exists(datasetId)) {
      throw new Error(`Knowledge base with ID "${datasetId}" not found`)
    }

    return apiRequest(`/datasets/${datasetId}/documents?page=${page}&page_size=${pageSize}`)
  }

  // Validate if a file is a markdown file
  static validateMarkdownFile(file: File): boolean {
    const allowedTypes = ['text/markdown', 'text/x-markdown', 'application/x-markdown']
    const allowedExtensions = ['.md', '.markdown']
    
    // Check file type
    if (allowedTypes.includes(file.type)) {
      return true
    }
    
    // Check file extension
    const fileName = file.name.toLowerCase()
    return allowedExtensions.some(ext => fileName.endsWith(ext))
  }

  // Get file size in MB
  static getFileSizeMB(file: File): number {
    return file.size / (1024 * 1024)
  }
}