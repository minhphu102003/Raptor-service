import { useState, useCallback } from 'react'

interface UseCopyToClipboardOptions {
  successDuration?: number
}

interface UseCopyToClipboardReturn {
  isCopied: boolean
  copyToClipboard: (text: string) => Promise<boolean>
}

export const useCopyToClipboard = (
  options: UseCopyToClipboardOptions = {}
): UseCopyToClipboardReturn => {
  const { successDuration = 2000 } = options
  const [isCopied, setIsCopied] = useState(false)

  const copyToClipboard = useCallback(
    async (text: string): Promise<boolean> => {
      try {
        if (navigator.clipboard?.writeText) {
          await navigator.clipboard.writeText(text)
        } else {
          // Fallback for older browsers
          const textArea = document.createElement('textarea')
          textArea.value = text
          textArea.style.position = 'fixed'
          textArea.style.left = '-999999px'
          textArea.style.top = '-999999px'
          document.body.appendChild(textArea)
          textArea.focus()
          textArea.select()
          document.execCommand('copy')
          document.body.removeChild(textArea)
        }

        setIsCopied(true)
        setTimeout(() => setIsCopied(false), successDuration)
        return true
      } catch (error) {
        console.error('Failed to copy to clipboard:', error)
        setIsCopied(false)
        return false
      }
    },
    [successDuration]
  )

  return { isCopied, copyToClipboard }
}