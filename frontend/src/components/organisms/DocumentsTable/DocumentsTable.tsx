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
  id: string
  name: string
  chunkNumber: number
  uploadDate: string
  chunkingMethod: string
  enabled: boolean
  parsingStatus: 'SUCCESS' | 'PROCESSING' | 'ERROR'
}

interface DocumentsTableProps {
  onAddDocument: () => void
  onRenameDocument?: (documentId: string, newName: string) => void
  onEditChunkingMethod?: (documentId: string, newMethod: string) => void
  onDeleteDocument?: (documentId: string) => void
  onDownloadDocument?: (documentId: string) => void
  className?: string
}

// Mock data - replace with real data from API
const mockDocuments: Document[] = [
  {
    id: '1',
    name: '20250319-MÔ TÂ...',
    chunkNumber: 29,
    uploadDate: '13/08/2025 17:01:11',
    chunkingMethod: 'General',
    enabled: true,
    parsingStatus: 'SUCCESS'
  },
  {
    id: '2', 
    name: '20250319-MÔ TÂ...',
    chunkNumber: 37,
    uploadDate: '13/08/2025 09:00:48',
    chunkingMethod: 'General',
    enabled: true,
    parsingStatus: 'SUCCESS'
  }
]

export const DocumentsTable = ({ 
  onAddDocument, 
  onRenameDocument,
  onEditChunkingMethod,
  onDeleteDocument,
  onDownloadDocument,
  className 
}: DocumentsTableProps) => {
  const [searchQuery, setSearchQuery] = useState('')
  const [documents, setDocuments] = useState<Document[]>(mockDocuments)

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
    setDocuments(prev => 
      prev.map(doc => 
        doc.id === documentId 
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

  const filteredDocuments = documents.filter(doc =>
    doc.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className={`space-y-4 ${className || ''}`}>
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
            <TableRow key={document.id}>
              <TableCell>
                <Text className="text-blue-600 font-medium cursor-pointer hover:underline text-base">
                  {document.name}
                </Text>
              </TableCell>
              <TableCell>
                <Text className="text-base">{document.chunkNumber}</Text>
              </TableCell>
              <TableCell>
                <Text className="text-gray-600 text-base">{document.uploadDate}</Text>
              </TableCell>
              <TableCell>
                <Text className="text-base">{document.chunkingMethod}</Text>
              </TableCell>
              <TableCell>
                <Switch
                  isSelected={document.enabled}
                  onValueChange={() => handleToggleEnabled(document.id)}
                  size="sm"
                />
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Chip
                    color={getStatusColor(document.parsingStatus)}
                    variant="flat"
                    size="md"
                    className="text-sm font-medium"
                  >
                    {document.parsingStatus}
                  </Chip>
                  {document.parsingStatus === 'SUCCESS' && (
                    <ReloadIcon className="w-4 h-4 text-green-500" />
                  )}
                </div>
              </TableCell>
              <TableCell>
                <ActionButtons
                  documentId={document.id}
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

      {/* Pagination - moved closer to table */}
      {/* Alternative using CSS classes - replace inline styles with className="pagination-btn" */}
      <div className="flex justify-between items-center mt-2">
        <Text className="text-gray-600 text-base pl-1">Total {filteredDocuments.length}</Text>
        <div className="flex items-center gap-2">
          <Button variant="bordered" size="md" disabled className="!w-10 !min-w-10 !p-0 tw-w-10 tw-p-0">
            &lt;
          </Button>
          <Button color="primary" size="md" className="!w-10 !min-w-10 tw-w-10">
            1
          </Button>
          <Button variant="bordered" size="md" disabled className="!w-10 !min-w-10 tw-w-10">
            &gt;
          </Button>
          <Dropdown>
            <DropdownTrigger>
              <Button variant="bordered" size="md" endContent={<ChevronDownIcon className="w-4 h-4" />}>
                10 / page
              </Button>
            </DropdownTrigger>
            <DropdownMenu>
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