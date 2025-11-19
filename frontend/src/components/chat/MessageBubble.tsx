import { useState } from 'react';
import { Copy, Check, Edit2, FileText, ThumbsUp, ThumbsDown } from 'lucide-react';
import type { Message } from '@/types';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { format } from 'date-fns';
import { MarkdownRenderer } from './MarkdownRenderer';
import { feedbackService } from '@/services/feedbackService';
import { useToast } from '@/hooks/use-toast';
import type { FeedbackType } from '@/types/feedback';

interface MessageBubbleProps {
  message: Message;
  conversationId?: string;
  onEdit?: (messageId: string) => void;
}

export function MessageBubble({ message, conversationId, onEdit }: MessageBubbleProps) {
  const [copiedMessage, setCopiedMessage] = useState(false);
  const [feedback, setFeedback] = useState<FeedbackType | null>(null);
  const [isSubmittingFeedback, setIsSubmittingFeedback] = useState(false);
  const { toast } = useToast();

  const isUser = message.role === 'user';

  const handleCopyMessage = async () => {
    await navigator.clipboard.writeText(message.content);
    setCopiedMessage(true);
    setTimeout(() => setCopiedMessage(false), 2000);
  };

  const handleFeedback = async (feedbackType: FeedbackType) => {
    if (!conversationId || isSubmittingFeedback) return;

    setIsSubmittingFeedback(true);
    try {
      await feedbackService.submitMessageFeedback({
        conversation_id: conversationId,
        message_id: message.message_id,
        feedback_type: feedbackType,
      });
      setFeedback(feedbackType);
      // Silent success - no toast needed for one-click action
    } catch (error) {
      console.error('Failed to submit feedback:', error);
      toast({
        title: 'Fehler',
        description: 'Feedback konnte nicht gesendet werden',
        variant: 'destructive',
      });
    } finally {
      setIsSubmittingFeedback(false);
    }
  };

  return (
    <div
      className={cn(
        'flex w-full gap-4 p-4 group animate-fade-in',
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
            'rounded-xl px-5 py-3.5 shadow-premium-sm border transition-all duration-200',
            isUser
              ? 'bg-gradient-to-br from-primary to-primary/90 text-primary-foreground border-primary/20 shadow-primary/10'
              : 'bg-card dark:bg-card/80 border-border/50 hover:shadow-premium-md hover:border-border'
          )}
        >
          <MarkdownRenderer content={message.content} />

          {message.edited && (
            <p className="text-xs opacity-70 mt-2 italic">
              (edited)
            </p>
          )}
        </div>

        <div className="flex items-center gap-2 text-xs text-muted-foreground">
          <span className="font-medium">{format(new Date(message.timestamp), 'PPp')}</span>

          {message.metadata?.response_time_ms && (
            <span className="flex items-center gap-1">
              <span className="inline-block w-1 h-1 rounded-full bg-muted-foreground/50"></span>
              <span className="font-mono">{message.metadata.response_time_ms}ms</span>
            </span>
          )}

          <div className="opacity-0 group-hover:opacity-100 transition-all duration-200 flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-7 w-7 hover:bg-accent/10"
              onClick={handleCopyMessage}
              aria-label="Copy message"
            >
              {copiedMessage ? (
                <Check className="h-3.5 w-3.5 text-success" />
              ) : (
                <Copy className="h-3.5 w-3.5" />
              )}
            </Button>

            {isUser && onEdit && (
              <Button
                variant="ghost"
                size="icon"
                className="h-7 w-7 hover:bg-accent/10"
                onClick={() => onEdit(message.message_id)}
                aria-label="Edit message"
              >
                <Edit2 className="h-3.5 w-3.5" />
              </Button>
            )}

            {!isUser && conversationId && (
              <>
                <Button
                  variant="ghost"
                  size="icon"
                  className={cn(
                    "h-7 w-7 hover:bg-accent/10",
                    feedback === 'helpful' && "text-success"
                  )}
                  onClick={() => handleFeedback('helpful')}
                  disabled={isSubmittingFeedback || feedback !== null}
                  aria-label="Helpful"
                >
                  <ThumbsUp className="h-3.5 w-3.5" />
                </Button>

                <Button
                  variant="ghost"
                  size="icon"
                  className={cn(
                    "h-7 w-7 hover:bg-accent/10",
                    feedback === 'not_helpful' && "text-destructive"
                  )}
                  onClick={() => handleFeedback('not_helpful')}
                  disabled={isSubmittingFeedback || feedback !== null}
                  aria-label="Not helpful"
                >
                  <ThumbsDown className="h-3.5 w-3.5" />
                </Button>
              </>
            )}
          </div>
        </div>

        {!isUser && message.metadata?.sources && message.metadata.sources.length > 0 && (
          <div className="flex flex-wrap gap-2 mt-2">
            {message.metadata.sources.map((source, index) => (
              <div
                key={index}
                className="flex items-center gap-1.5 text-xs bg-muted/50 hover:bg-muted px-2.5 py-1.5 rounded-lg border border-border/50 transition-colors"
              >
                <FileText className="h-3.5 w-3.5 text-primary" />
                <span className="font-medium">{source}</span>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
