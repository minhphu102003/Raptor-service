import { useRef, useEffect, useCallback } from 'react';
import type { RefObject } from 'react';

interface UseTextareaAutoResizeReturn {
  textareaRef: RefObject<HTMLTextAreaElement>;
}

export const useTextareaAutoResize = (maxLines: number = 4): UseTextareaAutoResizeReturn => {
  const textareaRef = useRef<HTMLTextAreaElement>(null);
  const lineHeightRef = useRef<number>(0);
  const rafRef = useRef<number | null>(null);
  const minHeightRef = useRef<number>(0);
  
  const resizeTextarea = useCallback(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;
    
    // Cancel any pending animation frame
    if (rafRef.current) {
      cancelAnimationFrame(rafRef.current);
    }
    
    // Schedule resize for next animation frame
    rafRef.current = requestAnimationFrame(() => {
      // Get line height only once for better performance
      if (!lineHeightRef.current) {
        const computedStyle = window.getComputedStyle(textarea);
        lineHeightRef.current = parseInt(computedStyle.lineHeight) || 20;
      }
      
      // Get min height (single line height) only once
      if (!minHeightRef.current) {
        minHeightRef.current = lineHeightRef.current + 4; // Add some padding
      }
      
      const lineHeight = lineHeightRef.current;
      const maxHeight = lineHeight * maxLines;
      const minHeight = minHeightRef.current;
      
      // Cache current styles to avoid unnecessary DOM writes
      const currentHeight = textarea.style.height;
      const currentOverflow = textarea.style.overflowY;
      
      // Create a hidden clone to measure the content height accurately
      const clone = textarea.cloneNode() as HTMLTextAreaElement;
      clone.style.position = 'absolute';
      clone.style.visibility = 'hidden';
      clone.style.height = 'auto';
      clone.style.width = textarea.offsetWidth + 'px';
      clone.style.overflow = 'hidden';
      clone.style.whiteSpace = 'pre-wrap';
      clone.style.wordWrap = 'break-word';
      
      document.body.appendChild(clone);
      const contentHeight = clone.scrollHeight;
      document.body.removeChild(clone);
      
      // Calculate new dimensions with more stable approach
      let newHeight = Math.max(minHeight, contentHeight);
      let overflow = 'hidden';
      
      // Apply constraints
      if (newHeight > maxHeight) {
        newHeight = maxHeight;
        overflow = 'auto';
      }
      
      // Round to nearest pixel to prevent sub-pixel rendering issues
      newHeight = Math.round(newHeight);
      
      // Only update if values actually changed (with small tolerance to prevent micro-changes)
      const heightDiff = Math.abs(parseFloat(currentHeight || '0') - newHeight);
      if (heightDiff > 1) {
        textarea.style.height = `${newHeight}px`;
      }
      if (currentOverflow !== overflow) {
        textarea.style.overflowY = overflow;
      }
    });
  }, [maxLines]);

  useEffect(() => {
    const textarea = textareaRef.current;
    if (!textarea) return;

    // Attach event listeners
    const handleInput = () => {
      // Throttle by canceling previous RAF and scheduling a new one
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
      rafRef.current = requestAnimationFrame(resizeTextarea);
    };
    
    const handlePasteOrCut = () => {
      // Delay resize for paste/cut operations to ensure content is updated
      setTimeout(resizeTextarea, 0);
    };
    
    // Also handle window resize events
    const handleWindowResize = () => {
      // Reset cached values when window resizes
      lineHeightRef.current = 0;
      minHeightRef.current = 0;
      resizeTextarea();
    };
    
    textarea.addEventListener('input', handleInput);
    textarea.addEventListener('paste', handlePasteOrCut);
    textarea.addEventListener('cut', handlePasteOrCut);
    window.addEventListener('resize', handleWindowResize);
    
    // Initial resize
    resizeTextarea();

    // Cleanup
    return () => {
      if (rafRef.current) {
        cancelAnimationFrame(rafRef.current);
      }
      textarea.removeEventListener('input', handleInput);
      textarea.removeEventListener('paste', handlePasteOrCut);
      textarea.removeEventListener('cut', handlePasteOrCut);
      window.removeEventListener('resize', handleWindowResize);
    };
  }, [resizeTextarea]);

  return { textareaRef: textareaRef as RefObject<HTMLTextAreaElement> };
};