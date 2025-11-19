import { useState, useRef, useEffect } from 'react';
import { Textarea } from '@/components/ui/textarea';
import { Button } from '@/components/ui/button';
import { Send } from 'lucide-react';
import { cn } from '@/lib/utils';

interface MessageInputProps {
  onSend: (message: string) => void;
  disabled?: boolean;
  placeholder?: string;
}

export function MessageInput({
  onSend,
  disabled = false,
  placeholder = 'Type your message here...',
}: MessageInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const maxLength = 2000;
  const showCounter = message.length >= 1800;

  useEffect(() => {
    if (textareaRef.current) {
      // Reset height to auto to get the correct scrollHeight
      textareaRef.current.style.height = 'auto';
      // Set height based on scrollHeight, max 5 lines (approx 120px)
      const newHeight = Math.min(textareaRef.current.scrollHeight, 120);
      textareaRef.current.style.height = `${newHeight}px`;
    }
  }, [message]);

  const handleSubmit = () => {
    if (message.trim() && !disabled) {
      onSend(message.trim());
      setMessage('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    } else if (e.key === 'Escape') {
      // Clear input on Escape
      e.preventDefault();
      setMessage('');
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  return (
    <div className="border-t border-border/50 bg-gradient-subtle backdrop-blur-sm p-6">
      <div className="max-w-4xl mx-auto">
        <div className="relative">
          <Textarea
            ref={textareaRef}
            value={message}
            onChange={(e) => {
              if (e.target.value.length <= maxLength) {
                setMessage(e.target.value);
              }
            }}
            onKeyDown={handleKeyDown}
            placeholder={placeholder}
            disabled={disabled}
            className={cn(
              'min-h-[60px] max-h-[120px] resize-none pr-28 rounded-xl border-2 border-border/50 focus:border-primary/50 shadow-premium-sm transition-all duration-200',
              disabled && 'opacity-50 cursor-not-allowed'
            )}
            aria-label="Message input"
          />
          <div className="absolute bottom-3 right-3 flex items-center gap-2">
            {showCounter && (
              <span
                className={cn(
                  'text-xs font-medium px-2 py-1 rounded-md',
                  message.length >= maxLength
                    ? 'text-destructive bg-destructive/10'
                    : 'text-muted-foreground bg-muted/50'
                )}
                aria-live="polite"
              >
                {message.length}/{maxLength}
              </span>
            )}
            <Button
              onClick={handleSubmit}
              disabled={!message.trim() || disabled}
              size="icon"
              variant="accent"
              aria-label="Send message"
              className="shadow-premium-md hover:shadow-premium-lg"
            >
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>
        <p className="text-xs text-muted-foreground mt-3 flex items-center gap-2">
          <span className="inline-block w-1.5 h-1.5 rounded-full bg-accent/50"></span>
          <kbd className="px-1.5 py-0.5 bg-muted rounded text-xs">Enter</kbd> zum Senden •
          <kbd className="px-1.5 py-0.5 bg-muted rounded text-xs">Shift+Enter</kbd> für neue Zeile •
          <kbd className="px-1.5 py-0.5 bg-muted rounded text-xs">Esc</kbd> zum Löschen
        </p>
      </div>
    </div>
  );
}
