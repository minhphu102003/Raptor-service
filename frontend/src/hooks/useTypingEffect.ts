import { useState, useEffect, useRef } from 'react';

interface UseTypingEffectProps {
  text: string;
  speed?: number;
  enabled?: boolean;
}

export const useTypingEffect = ({ 
  text, 
  speed = 0, // Set to 0 for nearly instant typing effect
  enabled = true 
}: UseTypingEffectProps) => {
  const [displayText, setDisplayText] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const indexRef = useRef(0);
  const timeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  useEffect(() => {
    // Clear any existing timeouts
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    // If typing effect is disabled or text is empty, show full text immediately
    if (!enabled || !text) {
      setDisplayText(text || '');
      setIsTyping(false);
      return;
    }

    // If this is a typing message, start typing effect
    if (text === 'typing') {
      setDisplayText('');
      setIsTyping(true);
      return;
    }

    // For regular text, start typing effect
    indexRef.current = 0;
    setDisplayText('');
    setIsTyping(true);

    const typeText = () => {
      if (indexRef.current < text.length) {
        setDisplayText(text.slice(0, indexRef.current + 1));
        indexRef.current++;
        timeoutRef.current = setTimeout(typeText, speed);
      } else {
        setIsTyping(false);
      }
    };

    timeoutRef.current = setTimeout(typeText, speed);

    // Cleanup function
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, [text, speed, enabled]);

  return { displayText, isTyping };
};