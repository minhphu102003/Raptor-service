import { apiRequest } from './api'
import { KnowledgeBaseService } from './knowledgeBaseService'

export interface UploadDocumentData {
  file: File
  datasetId: string
  source?: string
  tags?: string[]
  extraMeta?: Record<string, unknown>
  buildTree?: boolean
  summaryLlm?: string
  vectorIndex?: Record<string, unknown>
  upsertMode?: 'upsert' | 'replace' | 'skip_duplicates'
}

export interface DocumentUploadResponse {
  code: number
  data: {
    doc_id: string
    dataset_id: string
    status: string
    chunks: number
    indexed: {
      upserted: number
    }
    tree_id?: string
    checksum: string
  }
}

export class DocumentService {
  // Upload a document to a knowledge base (using UUID as dataset_id)
  static async uploadDocument(data: UploadDocumentData): Promise<DocumentUploadResponse> {
    // Verify the knowledge base exists in localStorage
    if (!KnowledgeBaseService.exists(data.datasetId)) {
      throw new Error(`Knowledge base with ID "${data.datasetId}" not found`)
    }

    // Prepare form data
    const formData = new FormData()
    formData.append('file', data.file)
    formData.append('dataset_id', data.datasetId)
    
    if (data.source) {
      formData.append('source', data.source)
    }
    
    if (data.tags && data.tags.length > 0) {
      data.tags.forEach(tag => formData.append('tags', tag))
    }
    
    if (data.extraMeta) {
      formData.append('extra_meta', JSON.stringify(data.extraMeta))
    }
    
    if (data.buildTree !== undefined) {
      formData.append('build_tree', data.buildTree.toString())
    }
    
    if (data.summaryLlm) {
      formData.append('summary_llm', data.summaryLlm)
    }
    
    if (data.vectorIndex) {
      formData.append('vector_index', JSON.stringify(data.vectorIndex))
    }
    
    if (data.upsertMode) {
      formData.append('upsert_mode', data.upsertMode)
    }

    try {
      // Call the upload API
      const response = await fetch(`http://localhost:8000/v1/documents/ingest-markdown`, {
        method: 'POST',
        body: formData,
      })

      if (!response.ok) {
        const errorText = await response.text()
        throw new Error(`Upload failed: ${response.status} ${response.statusText} - ${errorText}`)
      }

      const result: DocumentUploadResponse = await response.json()

      // Update document count in localStorage
      KnowledgeBaseService.incrementDocumentCount(data.datasetId)

      return result
    } catch (error) {
      console.error('Document upload failed:', error)
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