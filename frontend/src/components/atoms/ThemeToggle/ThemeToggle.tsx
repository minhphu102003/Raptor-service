import { Button } from '@heroui/react'
import { SunIcon, MoonIcon } from '@radix-ui/react-icons'
import { useState } from 'react'

interface ThemeToggleProps {
  className?: string
}

export const ThemeToggle = ({ className }: ThemeToggleProps) => {
  const [isDark, setIsDark] = useState(false)

  const toggleTheme = () => {
    setIsDark(!isDark)
    // In a real app, you would update the theme context here
  }

  return (
    <Button
      variant="ghost"
      size="sm"
      isIconOnly
      className={`text-gray-600 hover:text-gray-900 ${className || ''}`}
      onClick={toggleTheme}
    >
      {isDark ? (
        <SunIcon className="w-4 h-4" />
      ) : (
        <MoonIcon className="w-4 h-4" />
      )}
    </Button>
  )
}