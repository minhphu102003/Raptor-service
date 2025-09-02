import { useState, useCallback } from 'react'
import { DocumentService } from '../services'
import { useToast } from './useToast'

export interface UploadFileData {
  file: File
  source?: string
  tags?: string[]
  extraMeta?: string // JSON string instead of Record<string, any>
  buildTree?: boolean
  summaryLLM?: string
  vectorIndex?: string // JSON string instead of Record<string, any>
  upsertMode?: 'upsert' | 'replace' | 'skip_duplicates'
}

export interface UseDocumentUploadOptions {
  datasetId: string
  onSuccess?: (uploadedFiles: string[]) => void
  onError?: (error: Error) => void
}

export interface UseDocumentUploadReturn {
  uploadDocuments: (files: UploadFileData[]) => Promise<void>
  isUploading: boolean
  uploadProgress: Record<string, number>
  validateMarkdownFile: (file: File) => { isValid: boolean; error?: string }
  getFileSizeMB: (file: File) => number
}

export const useDocumentUpload = ({
  datasetId,
  onSuccess,
  onError
}: UseDocumentUploadOptions): UseDocumentUploadReturn => {
  const [isUploading, setIsUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState<Record<string, number>>({})
  const toast = useToast()

  // Frontend validation for Markdown files
  const validateMarkdownFile = useCallback((file: File): { isValid: boolean; error?: string } => {
    // Check file extension
    const fileName = file.name.toLowerCase()
    if (!fileName.endsWith('.md') && !fileName.endsWith('.markdown')) {
      return {
        isValid: false,
        error: 'File must have .md or .markdown extension'
      }
    }

    // Check file size (max 10MB)
    const maxSizeBytes = 10 * 1024 * 1024 // 10MB
    if (file.size > maxSizeBytes) {
      return {
        isValid: false,
        error: `File size (${(file.size / 1024 / 1024).toFixed(2)}MB) exceeds maximum limit of 10MB`
      }
    }

    // Check if file is empty
    if (file.size === 0) {
      return {
        isValid: false,
        error: 'File cannot be empty'
      }
    }

    // Basic MIME type check (though browsers may not set this correctly for .md files)
    const allowedMimeTypes = [
      'text/markdown',
      'text/plain',
      'text/x-markdown',
      'application/octet-stream' // Some browsers use this for .md files
    ]
    
    if (file.type && !allowedMimeTypes.includes(file.type)) {
      console.warn(`Unexpected MIME type: ${file.type} for file: ${file.name}`)
      // Don't fail validation based on MIME type alone, as it's unreliable for .md files
    }

    return { isValid: true }
  }, [])

  const getFileSizeMB = useCallback((file: File): number => {
    return file.size / (1024 * 1024)
  }, [])

  const uploadDocuments = useCallback(async (files: UploadFileData[]): Promise<void> => {
    if (!datasetId) {
      throw new Error('Dataset ID is required for upload')
    }

    if (files.length === 0) {
      throw new Error('No files selected for upload')
    }

    // Debug: Log input data
    console.log('[useDocumentUpload] UploadDocuments called with:', { datasetId, filesCount: files.length, files })

    setIsUploading(true)
    setUploadProgress({})

    const uploadedFiles: string[] = []
    const failedFiles: { fileName: string; error: string }[] = []

    try {
      for (let i = 0; i < files.length; i++) {
        const fileData = files[i]
        const fileName = fileData.file.name

        try {
          // Frontend validation
          const validation = validateMarkdownFile(fileData.file)
          if (!validation.isValid) {
            throw new Error(validation.error || 'File validation failed')
          }

          // Update progress
          setUploadProgress(prev => ({ ...prev, [fileName]: 0 }))

          // Debug: Log each file upload data
          console.log(`[useDocumentUpload] Processing file ${i + 1}/${files.length}:`, {
            fileName: fileName,
            fileSize: fileData.file.size,
            fileType: fileData.file.type,
            datasetId: datasetId,
            source: fileData.source,
            tags: fileData.tags,
            extraMeta: fileData.extraMeta,
            buildTree: fileData.buildTree,
            summaryLLM: fileData.summaryLLM,
            vectorIndex: fileData.vectorIndex,
            upsertMode: fileData.upsertMode
          })

          // Prepare upload data according to the API specification
          const uploadPayload = {
            file: fileData.file,
            datasetId: datasetId,
            source: fileData.source || `Frontend upload: ${fileName}`,
            tags: fileData.tags || ['frontend-upload'],
            extraMeta: fileData.extraMeta ? fileData.extraMeta : JSON.stringify({
              uploadedBy: 'frontend',
              timestamp: new Date().toISOString(),
              originalFileName: fileName
            }),
            buildTree: fileData.buildTree ?? true,
            summaryLLM: fileData.summaryLLM || 'DeepSeek-V3',
            vectorIndex: fileData.vectorIndex ? fileData.vectorIndex : undefined,
            upsertMode: fileData.upsertMode || 'upsert'
          }

          // Debug: Log prepared upload payload
          console.log(`[useDocumentUpload] Prepared upload payload for ${fileName}:`, uploadPayload)

          // Simulate progress during upload
          setUploadProgress(prev => ({ ...prev, [fileName]: 25 }))

          // Call the document service to upload
          const result = await DocumentService.uploadDocument(uploadPayload)
          
          // Complete progress
          setUploadProgress(prev => ({ ...prev, [fileName]: 100 }))
          
          uploadedFiles.push(result.document_id || fileName)
          
          toast.success(
            `Document uploaded successfully`,
            `"${fileName}" has been processed and added to the knowledge base`
          )

        } catch (error) {
          const errorMessage = error instanceof Error ? error.message : 'Unknown error occurred'
          failedFiles.push({ fileName, error: errorMessage })
          
          console.error(`Failed to upload ${fileName}:`, error)
          
          toast.error(
            `Failed to upload "${fileName}"`,
            errorMessage
          )
        }
      }

      // Handle results
      if (uploadedFiles.length > 0) {
        onSuccess?.(uploadedFiles)
      }

      if (failedFiles.length > 0) {
        const errorSummary = `${failedFiles.length} file(s) failed to upload: ${failedFiles.map(f => f.fileName).join(', ')}`
        const combinedError = new Error(errorSummary)
        onError?.(combinedError)
      }

      // Show final summary if multiple files
      if (files.length > 1) {
        if (uploadedFiles.length === files.length) {
          toast.success(
            'All documents uploaded successfully',
            `${uploadedFiles.length} file(s) processed and added to the knowledge base`
          )
        } else if (uploadedFiles.length > 0) {
          toast.warning(
            'Partial upload completed',
            `${uploadedFiles.length} of ${files.length} file(s) uploaded successfully`
          )
        }
      }

    } catch (error) {
      console.error('Upload process failed:', error)
      const errorMessage = error instanceof Error ? error.message : 'Upload process failed'
      toast.error('Upload failed', errorMessage)
      onError?.(error instanceof Error ? error : new Error(errorMessage))
    } finally {
      setIsUploading(false)
      // Clear progress after a delay
      setTimeout(() => setUploadProgress({}), 2000)
    }
  }, [datasetId, validateMarkdownFile, toast, onSuccess, onError])

  return {
    uploadDocuments,
    isUploading,
    uploadProgress,
    validateMarkdownFile,
    getFileSizeMB
  }
}