import React from 'react'
import {
  Table,
  TableHeader,
  TableBody,
  TableColumn,
  TableRow,
  TableCell,
  Button,
  Switch,
  Chip,
  Input,
  Dropdown,
  DropdownTrigger,
  DropdownMenu,
  DropdownItem
} from '@heroui/react'
import { Text } from '@radix-ui/themes'
import {
  PlusIcon,
  MagnifyingGlassIcon,
  ChevronDownIcon,
  ReloadIcon
} from '@radix-ui/react-icons'
import { useState } from 'react'
import { ActionButtons } from '../../molecules'

interface Document {
  doc_id: string
  source: string
  tags: string[] | null
  extra_meta: Record<string, unknown> | null
  checksum: string
  created_at: string
  // Optional properties for UI state
  enabled?: boolean
  chunkingMethod?: string
  chunkNumber?: number
  parsingStatus?: 'SUCCESS' | 'PROCESSING' | 'ERROR'
}

interface PaginationInfo {
  page: number
  page_size: number
  total: number
  pages: number
}

interface DocumentsTableProps {
  documents?: Document[]
  pagination?: PaginationInfo | null
  loading?: boolean
  error?: string | null
  onAddDocument: () => void
  onRenameDocument?: (documentId: string, newName: string) => void
  onEditChunkingMethod?: (documentId: string, newMethod: string) => void
  onDeleteDocument?: (documentId: string) => void
  onDownloadDocument?: (documentId: string) => void
  onPageChange?: (page: number) => void
  onPageSizeChange?: (pageSize: number) => void
  className?: string
}



export const DocumentsTable = ({
  documents = [],
  pagination,
  loading = false,
  error,
  onAddDocument,
  onRenameDocument,
  onEditChunkingMethod,
  onDeleteDocument,
  onDownloadDocument,
  onPageChange,
  onPageSizeChange,
  className
}: DocumentsTableProps) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [localDocuments, setLocalDocuments] = useState<Document[]>([])

  // Update local documents when props change
  React.useEffect(() => {
    if (documents) {
      // Transform API documents to include UI state
      const transformedDocs = documents.map(doc => ({
        ...doc,
        enabled: doc.enabled ?? true,
        chunkingMethod: doc.chunkingMethod ?? 'General',
        chunkNumber: doc.chunkNumber ?? 0,
        parsingStatus: (doc.parsingStatus ?? 'SUCCESS') as 'SUCCESS' | 'PROCESSING' | 'ERROR'
      }))
      setLocalDocuments(transformedDocs)
    }
  }, [documents])

  // Helper function to get document name from source
  const getDocumentName = (source: string) => {
    const parts = source.split('/')
    const filename = parts[parts.length - 1]
    // Remove .md extension and truncate if too long
    const nameWithoutExt = filename.replace('.md', '')
    return nameWithoutExt.length > 20 ? nameWithoutExt.substring(0, 20) + '...' : nameWithoutExt
  }

  // Helper function to format date
  const formatDate = (dateString: string) => {
    const date = new Date(dateString)
    return date.toLocaleString('en-GB', {
      day: '2-digit',
      month: '2-digit',
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
      second: '2-digit'
    })
  }

  const handleRename = (documentId: string) => {
    const newName = prompt('Enter new name:');
    if (newName && onRenameDocument) {
      onRenameDocument(documentId, newName);
    }
  };

  const handleEditChunking = (documentId: string) => {
    const newMethod = prompt('Enter new chunking method:');
    if (newMethod && onEditChunkingMethod) {
      onEditChunkingMethod(documentId, newMethod);
    }
  };

  const handleDelete = (documentId: string) => {
    if (confirm('Are you sure you want to delete this document?')) {
      onDeleteDocument?.(documentId);
    }
  };

  const handleDownload = (documentId: string) => {
    onDownloadDocument?.(documentId);
  };

  const handleToggleEnabled = (documentId: string) => {
    setLocalDocuments(prev =>
      prev.map(doc =>
        doc.doc_id === documentId
          ? { ...doc, enabled: !doc.enabled }
          : doc
      )
    )
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return 'success'
      case 'PROCESSING':
        return 'warning'
      case 'ERROR':
        return 'danger'
      default:
        return 'default'
    }
  }

  const filteredDocuments = localDocuments.filter(doc => {
    const documentName = getDocumentName(doc.source)
    return documentName.toLowerCase().includes(searchQuery.toLowerCase())
  })

  return (
    <div className={`space-y-4 ${className || ''}`}>
      {/* Error State */}
      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <Text className="text-red-700">Error loading documents: {error}</Text>
        </div>
      )}

      {/* Header Actions */}
      <div className="flex flex-col sm:flex-row gap-4 justify-between items-start sm:items-center">
        <div className="flex gap-2">
          <Dropdown>
            <DropdownTrigger>
              <Button
                variant="bordered"
                endContent={<ChevronDownIcon className="w-4 h-4" />}
              >
                Bulk
              </Button>
            </DropdownTrigger>
            <DropdownMenu>
              <DropdownItem key="enable">Enable Selected</DropdownItem>
              <DropdownItem key="disable">Disable Selected</DropdownItem>
              <DropdownItem key="delete" className="text-danger">Delete Selected</DropdownItem>
            </DropdownMenu>
          </Dropdown>
        </div>

        <div className="flex flex-col sm:flex-row gap-3 w-full sm:w-auto">
          <Input
            placeholder="Search your files"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            startContent={<MagnifyingGlassIcon className="w-4 h-4 text-gray-400" />}
            className="sm:w-80"
            size="md"
          />
          <Button
            color="primary"
            startContent={<PlusIcon className="w-4 h-4" />}
            className="sm:w-auto w-full"
            onPress={onAddDocument}
          >
            Add file
          </Button>
        </div>
      </div>

      {/* Documents Table */}
      {loading ? (
        <div className="flex justify-center items-center py-12">
          <Text className="text-gray-500">Loading documents...</Text>
        </div>
      ) : (
        <Table
          aria-label="Documents table"
          selectionMode="multiple"
        >
          <TableHeader>
            <TableColumn className="text-base font-medium">Name</TableColumn>
            <TableColumn className="text-base font-medium">Chunk Number</TableColumn>
            <TableColumn className="text-base font-medium">Upload Date</TableColumn>
            <TableColumn className="text-base font-medium">Chunking method</TableColumn>
            <TableColumn className="text-base font-medium">Enable</TableColumn>
            <TableColumn className="text-base font-medium">Parsing Status</TableColumn>
            <TableColumn className="text-base font-medium">Actions</TableColumn>
          </TableHeader>
          <TableBody emptyContent={filteredDocuments.length === 0 ? "No documents found" : undefined}>
            {filteredDocuments.map((document) => (
              <TableRow key={document.doc_id}>
                <TableCell>
                  <Text className="text-blue-600 font-medium cursor-pointer hover:underline text-base">
                    {getDocumentName(document.source)}
                  </Text>
                </TableCell>
                <TableCell>
                  <Text className="text-base">{document.chunkNumber || 0}</Text>
                </TableCell>
                <TableCell>
                  <Text className="text-gray-600 text-base">{formatDate(document.created_at)}</Text>
                </TableCell>
              <TableCell>
                <Text className="text-base">{document.chunkingMethod || 'General'}</Text>
              </TableCell>
              <TableCell>
                <Switch
                  isSelected={document.enabled}
                  onValueChange={() => handleToggleEnabled(document.doc_id)}
                  size="sm"
                />
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Chip
                    color={getStatusColor(document.parsingStatus || 'SUCCESS')}
                    variant="flat"
                    size="md"
                    className="text-sm font-medium"
                  >
                    {document.parsingStatus || 'SUCCESS'}
                  </Chip>
                  {(document.parsingStatus || 'SUCCESS') === 'SUCCESS' && (
                    <ReloadIcon className="w-4 h-4 text-green-500" />
                  )}
                </div>
              </TableCell>
              <TableCell>
                <ActionButtons
                  documentId={document.doc_id}
                  onRename={handleRename}
                  onEditChunking={handleEditChunking}
                  onDownload={handleDownload}
                  onDelete={handleDelete}
                />
              </TableCell>
            </TableRow>
          ))}
        </TableBody>
      </Table>
    )}

      {/* Pagination */}
      <div className="flex justify-between items-center mt-2">
        <Text className="text-gray-600 text-base pl-1">
          Total {pagination?.total || filteredDocuments.length}
        </Text>
        <div className="flex items-center gap-2">
          <Button 
            variant="bordered" 
            size="md" 
            disabled={!pagination || pagination.page <= 1}
            className="!w-10 !min-w-10 !p-0 tw-w-10 tw-p-0"
            onPress={() => onPageChange && onPageChange(pagination!.page - 1)}
          >
            &lt;
          </Button>
          <Button color="primary" size="md" className="!w-10 !min-w-10 tw-w-10">
            {pagination?.page || 1}
          </Button>
          <Button 
            variant="bordered" 
            size="md" 
            disabled={!pagination || pagination.page >= pagination.pages}
            className="!w-10 !min-w-10 tw-w-10"
            onPress={() => onPageChange && onPageChange(pagination!.page + 1)}
          >
            &gt;
          </Button>
          <Dropdown>
            <DropdownTrigger>
              <Button variant="bordered" size="md" endContent={<ChevronDownIcon className="w-4 h-4" />}>
                {pagination?.page_size || 10} / page
              </Button>
            </DropdownTrigger>
            <DropdownMenu onAction={(key) => onPageSizeChange && onPageSizeChange(Number(key))}>
              <DropdownItem key="10">10 / page</DropdownItem>
              <DropdownItem key="25">25 / page</DropdownItem>
              <DropdownItem key="50">50 / page</DropdownItem>
            </DropdownMenu>
          </Dropdown>
        </div>
      </div>
    </div>
  )
}
