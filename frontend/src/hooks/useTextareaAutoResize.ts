import { useRef, useEffect } from 'react';

export const useTextareaAutoResize = (value: string, maxLines: number = 4) => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      const scrollHeight = textareaRef.current.scrollHeight;
      const lineHeight = parseInt(window.getComputedStyle(textareaRef.current).lineHeight);
      const maxHeight = lineHeight * maxLines;
      
      if (scrollHeight > maxHeight) {
        textareaRef.current.style.height = `${maxHeight}px`;
        textareaRef.current.style.overflowY = 'auto';
      } else {
        textareaRef.current.style.height = `${scrollHeight}px`;
        textareaRef.current.style.overflowY = 'hidden';
      }
    }
  }, [value, maxLines]);

  return textareaRef;
};