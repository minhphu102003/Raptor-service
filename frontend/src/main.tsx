import React from 'react'
import ReactDOM from 'react-dom/client'
import { HeroUIProvider } from '@heroui/react'
import { Theme } from '@radix-ui/themes'
import App from './App.tsx'
import './index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <Theme>
      <HeroUIProvider>
        <App />
      </HeroUIProvider>
    </Theme>
  </React.StrictMode>
)