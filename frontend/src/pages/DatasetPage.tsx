import { Heading, Text } from '@radix-ui/themes'
import { DatasetSidebar, AddDocumentModal } from '../components/molecules'
import { DocumentsTable } from '../components/organisms'
import { KnowledgePageTemplate } from '../components/templates'
import type { FileUploadItem } from '../components/molecules'
import { useState } from 'react'
import { motion } from 'framer-motion'

export const DatasetPage = () => {
  const [isAddModalOpen, setIsAddModalOpen] = useState(false)

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
        duration: 0.4,
        ease: "easeOut"
      }
    }
  }

  const handleAddDocuments = async (files: FileUploadItem[]) => {
    try {
      // TODO: Implement API call to upload documents
      console.log('Uploading documents:', files)
      
      // For now, just log the files
      // In a real implementation, you would call an API here
      // await uploadDocuments(datasetId, files)
      
      // Show success message
      alert(`${files.length} document(s) uploaded successfully!`)
    } catch (error) {
      console.error('Failed to upload documents:', error)
      throw error // Re-throw to let the modal handle the error state
    }
  }

  const handleRenameDocument = async (documentId: string, newName: string) => {
    try {
      // TODO: Implement API call to rename document
      console.log('Renaming document:', documentId, 'to:', newName)
      alert(`Document renamed to: ${newName}`)
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
        className="h-[calc(100vh-80px)] flex bg-gray-50"
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
          <div className="bg-white shadow-sm px-8 py-6">
            <Heading size="6" className="text-gray-900 mb-2 font-secondary-heading">
              Dataset
            </Heading>
            <Text className="text-gray-600">
              Please wait for your files to finish parsing before starting an AI-powered chat.
            </Text>
          </div>
          
          {/* Documents Table */}
          <div className="flex-1 overflow-auto p-8">
            <DocumentsTable 
              onAddDocument={() => setIsAddModalOpen(true)}
              onRenameDocument={handleRenameDocument}
              onEditChunkingMethod={handleEditChunkingMethod}
              onDeleteDocument={handleDeleteDocument}
              onDownloadDocument={handleDownloadDocument}
            />
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