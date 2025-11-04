import { useState } from 'react';
import { Copy, Check, Edit2, FileText } from 'lucide-react';
import type { Message } from '@/types';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { MarkdownRenderer } from './MarkdownRenderer';

interface MessageBubbleProps {
  message: Message;
  onEdit?: (messageId: string) => void;
}

export function MessageBubble({ message, onEdit }: MessageBubbleProps) {
  const [copiedMessage, setCopiedMessage] = useState(false);

  const isUser = message.role === 'user';

  const handleCopyMessage = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopiedMessage(true);
    setTimeout(() => setCopiedMessage(false), 2000);
  };

  return (
    <div
      className={cn(
        'flex w-full gap-4 p-4 group',
        isUser ? 'justify-end' : 'justify-start'
      )}
    >
      <div
        className={cn(
          'flex flex-col max-w-[80%] space-y-2',
          isUser ? 'items-end' : 'items-start'
        )}
      >
        <div
          className={cn(
            'rounded-lg px-4 py-3 shadow-sm border-2',
            isUser
              ? 'bg-blue-50 dark:bg-blue-950 border-blue-200 dark:border-blue-800'
              : 'bg-white dark:bg-gray-800 border-gray-200 dark:border-gray-700'
          )}
        >
          <MarkdownRenderer content={message.content} />

          {message.edited && (
            <p className="text-xs text-muted-foreground mt-2 italic">
              (edited)
            </p>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span>{format(new Date(message.timestamp), 'PPp')}</span>

          {message.metadata?.response_time_ms && (
            <span>• {message.metadata.response_time_ms}ms</span>
          )}

          <div className="opacity-0 group-hover:opacity-100 transition-opacity flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-6 w-6"
              onClick={handleCopyMessage}
              aria-label="Copy message"
            >
              {copiedMessage ? (
                <Check className="h-3 w-3" />
              ) : (
                <Copy className="h-3 w-3" />
              )}
            </Button>

            {isUser && onEdit && (
              <Button
                variant="ghost"
                size="icon"
                className="h-6 w-6"
                onClick={() => onEdit(message.message_id)}
                aria-label="Edit message"
              >
                <Edit2 className="h-3 w-3" />
              </Button>
            )}
          </div>
        </div>

        {!isUser && message.metadata?.sources && message.metadata.sources.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {message.metadata.sources.map((source, index) => (
              <div
                key={index}
                className="flex items-center gap-1 text-xs bg-muted px-2 py-1 rounded-md"
              >
                <FileText className="h-3 w-3" />
                <span>{source}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
