import { ReactNode } from 'react'
import { Header, Footer } from '../../organisms'

interface LandingPageTemplateProps {
  children: ReactNode
  className?: string
}

export const LandingPageTemplate = ({ children, className }: LandingPageTemplateProps) => {
  return (
    <div className={`min-h-screen bg-gradient-to-br from-slate-50 to-indigo-50 ${className || ''}`}>
      <Header />
      <main>
        {children}
      </main>
      <Footer />
    </div>
  )
}