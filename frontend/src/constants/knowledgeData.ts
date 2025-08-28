export interface KnowledgeBase {
  id: string
  title: string
  description: string
  documentCount: number
  createdAt: string
}

export const knowledgeBasesData: KnowledgeBase[] = [
  {
    id: '1',
    title: 'Product Documentation',
    description: 'Comprehensive documentation for all product features, API references, and user guides.',
    documentCount: 156,
    createdAt: '2 days ago'
  },
  {
    id: '2', 
    title: 'Technical Specifications',
    description: 'Detailed technical specifications, architecture diagrams, and system requirements.',
    documentCount: 89,
    createdAt: '1 week ago'
  },
  {
    id: '3',
    title: 'User Manuals',
    description: 'Step-by-step user manuals and tutorials for different user roles and workflows.',
    documentCount: 234,
    createdAt: '3 days ago'
  },
  {
    id: '4',
    title: 'Research Papers',
    description: 'Collection of research papers, whitepapers, and academic publications related to AI and ML.',
    documentCount: 67,
    createdAt: '5 days ago'
  },
  {
    id: '5',
    title: 'Meeting Notes',
    description: 'Meeting minutes, project updates, and decision records from team meetings.',
    documentCount: 423,
    createdAt: '1 day ago'
  },
  {
    id: '6',
    title: 'Legal Documents',
    description: 'Legal agreements, compliance documents, and regulatory information.',
    documentCount: 34,
    createdAt: '2 weeks ago'
  },
  {
    id: '7',
    title: 'Marketing Materials',
    description: 'Marketing content, presentations, case studies, and promotional materials.',
    documentCount: 178,
    createdAt: '4 days ago'
  },
  {
    id: '8',
    title: 'Training Resources',
    description: 'Training materials, onboarding guides, and educational content for new employees.',
    documentCount: 92,
    createdAt: '1 week ago'
  }
]