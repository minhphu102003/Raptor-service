import { Heading, Text } from '@radix-ui/themes'
import { DatasetSidebar, AddDocumentModal } from '../components/molecules'
import { DocumentsTable } from '../components/organisms'
import { KnowledgePageTemplate } from '../components/templates'
import type { FileUploadItem } from '../components/molecules'
import { useDatasetDocuments, useDatasets, useDocumentUpload } from '../hooks'
import { KnowledgeBaseService } from '../services'
import { useParams } from '@tanstack/react-router'
import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'

export const DatasetPage = () => {
  const { id: datasetId } = useParams({ from: '/dataset/$id' })
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(20)

  // Get dataset info from backend API
  const { datasets } = useDatasets()
  
  // Find the current dataset from backend data, fallback to localStorage if not found
  const dataset = useMemo(() => {
    const backendDataset = datasets.find(ds => ds.id === datasetId)
    if (backendDataset) {
      return {
        id: backendDataset.id,
        name: backendDataset.name || backendDataset.id,
        description: backendDataset.description || 'No description available',
        document_count: backendDataset.document_count,
        created_at: backendDataset.created_at
      }
    }
    
    // Fallback to localStorage if not found in backend
    const localKB = KnowledgeBaseService.getById(datasetId)
    if (localKB) {
      return {
        id: localKB.id,
        name: localKB.name,
        description: localKB.description,
        document_count: localKB.documentCount,
        created_at: localKB.createdAt
      }
    }
    
    return null
  }, [datasetId, datasets])

  // Fetch documents data from API using the UUID as dataset_id
  const { documents, pagination, loading, error, refetch } = useDatasetDocuments(
    datasetId,
    currentPage,
    pageSize
  )

  // Document upload hook with validation and API integration
  const {
    uploadDocuments,
    isUploading,
    uploadProgress,
    validateMarkdownFile,
    getFileSizeMB
  } = useDocumentUpload({
    datasetId,
    onSuccess: (uploadedFiles) => {
      console.log('Upload completed successfully:', uploadedFiles)
      refetch() // Refresh the documents list
    },
    onError: (error) => {
      console.error('Upload failed:', error)
      // Error handling is already done in the hook with toast notifications
    }
  })

  // Animation variants for simple fade-in effects
  const containerVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        duration: 0.5,
        staggerChildren: 0.2
      }
    }
  }

  const itemVariants = {
    hidden: { opacity: 0 },
    visible: {
      opacity: 1,
      transition: {
        duration: 0.4
      }
    }
  }

  const handlePageChange = (page: number) => {
    setCurrentPage(page)
  }

  const handlePageSizeChange = (newPageSize: number) => {
    setPageSize(newPageSize)
    setCurrentPage(1) // Reset to first page when changing page size
  }

  const handleAddDocuments = async (files: FileUploadItem[]) => {
    try {
      // Debug: Log input files
      console.log('[DatasetPage] handleAddDocuments called with files:', files)

      // Convert FileUploadItem[] to UploadFileData[] with enhanced metadata
      const uploadData = files.map(fileItem => ({
        file: fileItem.file,
        source: `Frontend upload: ${fileItem.file.name}`,
        tags: ['frontend-upload', 'user-content'],
        extraMeta: JSON.stringify({
          originalFileName: fileItem.file.name,
          uploadedBy: 'frontend-user',
          timestamp: new Date().toISOString(),
          fileSize: getFileSizeMB(fileItem.file),
          userAgent: navigator.userAgent
        }),
        buildTree: true,
        summaryLLM: 'DeepSeek-V3',
        vectorIndex: undefined, // Use default vector index settings
        upsertMode: 'upsert' as const
      }))

      // Debug: Log converted upload data
      console.log('[DatasetPage] Converted upload data:', uploadData)

      // Frontend validation before upload
      for (const fileData of uploadData) {
        const validation = validateMarkdownFile(fileData.file)
        if (!validation.isValid) {
          throw new Error(`File "${fileData.file.name}": ${validation.error}`)
        }
      }

      // Use the hook to upload documents
      await uploadDocuments(uploadData)
      
      // Success feedback is handled by the hook's toast notifications
    } catch (error) {
      console.error('[DatasetPage] Failed to add documents:', error)
      // Error feedback is handled by the hook's toast notifications
      throw error // Re-throw to let the modal handle the error state
    }
  }

  const handleRenameDocument = async (documentId: string, newName: string) => {
    try {
      // TODO: Implement API call to rename document
      console.log('Renaming document:', documentId, 'to:', newName)
      alert(`Document renamed to: ${newName}`)
      refetch() // Refresh the documents list
    } catch (error) {
      console.error('Failed to rename document:', error)
      alert('Failed to rename document')
    }
  }

  const handleEditChunkingMethod = async (documentId: string, newMethod: string) => {
    try {
      // TODO: Implement API call to update chunking method
      console.log('Updating chunking method for document:', documentId, 'to:', newMethod)
      alert(`Chunking method updated to: ${newMethod}`)
      refetch() // Refresh the documents list
    } catch (error) {
      console.error('Failed to update chunking method:', error)
      alert('Failed to update chunking method')
    }
  }

  const handleDeleteDocument = async (documentId: string) => {
    try {
      // TODO: Implement API call to delete document
      console.log('Deleting document:', documentId)
      alert('Document deleted successfully!')
      refetch() // Refresh the documents list
    } catch (error) {
      console.error('Failed to delete document:', error)
      alert('Failed to delete document')
    }
  }

  const handleDownloadDocument = async (documentId: string) => {
    try {
      // TODO: Implement API call to download document
      console.log('Downloading document:', documentId)
      alert('Download started!')
    } catch (error) {
      console.error('Failed to download document:', error)
      alert('Failed to download document')
    }
  }

  return (
    <KnowledgePageTemplate>
      <motion.div
        className="h-[calc(100vh-80px)] flex bg-gray-50 dark:bg-gray-900"
        variants={containerVariants}
        initial="hidden"
        animate="visible"
      >
        {/* Sidebar */}
        <motion.div variants={itemVariants}>
          <DatasetSidebar />
        </motion.div>

        {/* Main Content */}
        <motion.div
          className="flex-1 flex flex-col overflow-hidden"
          variants={itemVariants}
        >
          {/* Content Header */}
          <div className="bg-white dark:bg-gray-800 shadow-sm px-8 py-6 border-b border-gray-200 dark:border-gray-700">
            <Heading size="6" className="text-gray-900 dark:text-gray-100 mb-2 font-secondary-heading">
              {dataset ? dataset.name : datasetId}
            </Heading>
            <Text className="text-gray-600 dark:text-gray-400">
              {dataset ? dataset.description : 'Please wait for your files to finish parsing before starting an AI-powered chat.'}
            </Text>
            {pagination && (
              <Text className="text-sm text-gray-500 mt-1">
                Showing {documents.length} of {pagination.total} documents
              </Text>
            )}
            {dataset && (
              <Text className="text-sm text-gray-500 mt-1">
                Dataset ID: {dataset.id} • Created: {new Date(dataset.created_at).toLocaleDateString()}
                {dataset.document_count > 0 && ` • Total Documents: ${dataset.document_count}`}
              </Text>
            )}
          </div>

          {/* Documents Table */}
          <div className="flex-1 overflow-auto p-8">
            <DocumentsTable
              documents={documents}
              pagination={pagination}
              loading={loading || isUploading}
              error={error}
              onAddDocument={() => setIsAddModalOpen(true)}
              onRenameDocument={handleRenameDocument}
              onEditChunkingMethod={handleEditChunkingMethod}
              onDeleteDocument={handleDeleteDocument}
              onDownloadDocument={handleDownloadDocument}
              onPageChange={handlePageChange}
              onPageSizeChange={handlePageSizeChange}
            />
            
            {/* Upload Progress Indicator */}
            {isUploading && Object.keys(uploadProgress).length > 0 && (
              <div className="mt-4 p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200 dark:border-blue-800">
                <h4 className="text-sm font-medium text-blue-900 dark:text-blue-100 mb-2">
                  Uploading Documents...
                </h4>
                <div className="space-y-2">
                  {Object.entries(uploadProgress).map(([fileName, progress]) => (
                    <div key={fileName} className="flex items-center space-x-3">
                      <span className="text-xs text-blue-700 dark:text-blue-300 min-w-0 flex-1 truncate">
                        {fileName}
                      </span>
                      <div className="w-24 bg-blue-200 dark:bg-blue-800 rounded-full h-2">
                        <div 
                          className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                      <span className="text-xs text-blue-700 dark:text-blue-300 w-10 text-right">
                        {Math.round(progress)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </motion.div>

        {/* Add Document Modal */}
        <AddDocumentModal
          isOpen={isAddModalOpen}
          onClose={() => setIsAddModalOpen(false)}
          onSubmit={handleAddDocuments}
        />
      </motion.div>
    </KnowledgePageTemplate>
  )
}
