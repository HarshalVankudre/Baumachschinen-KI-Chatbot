import { useState } from 'react';
import { ThumbsUp, ThumbsDown, MessageSquare, Send, CheckCircle2 } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useTranslation } from 'react-i18next';

interface MessageFeedbackProps {
  messageId: string;
  onFeedbackSubmit?: (feedback: FeedbackData) => void;
  className?: string;
}

export interface FeedbackData {
  messageId: string;
  rating: 'positive' | 'negative';
  comment?: string;
}

export function MessageFeedback({ messageId, onFeedbackSubmit, className }: MessageFeedbackProps) {
  const { t } = useTranslation();
  const [selectedRating, setSelectedRating] = useState<'positive' | 'negative' | null>(null);
  const [showCommentField, setShowCommentField] = useState(false);
  const [comment, setComment] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isSubmitted, setIsSubmitted] = useState(false);

  const handleRatingClick = (rating: 'positive' | 'negative') => {
    if (isSubmitted) return;

    // Toggle rating or select new one
    if (selectedRating === rating) {
      setSelectedRating(null);
      setShowCommentField(false);
      setComment('');
    } else {
      setSelectedRating(rating);
      // Auto-expand comment field for negative feedback
      if (rating === 'negative') {
        setShowCommentField(true);
      }
    }
  };

  const handleSubmit = async () => {
    if (!selectedRating) return;

    setIsSubmitting(true);

    const feedbackData: FeedbackData = {
      messageId,
      rating: selectedRating,
      comment: comment.trim() || undefined,
    };

    // Simulate API call
    await new Promise(resolve => setTimeout(resolve, 500));

    onFeedbackSubmit?.(feedbackData);

    setIsSubmitting(false);
    setIsSubmitted(true);

    // Reset after showing confirmation
    setTimeout(() => {
      setIsSubmitted(false);
    }, 3000);
  };

  if (isSubmitted) {
    return (
      <div className={cn('flex items-center gap-2 opacity-0 animate-fade-in', className)}>
        <div className="flex items-center gap-2 text-sm text-success px-3 py-1.5 rounded-lg bg-success/10 border border-success/20">
          <CheckCircle2 className="h-4 w-4" />
          <span className="font-medium">{t('feedback.thankYou', 'Thank you for your feedback!')}</span>
        </div>
      </div>
    );
  }

  return (
    <div className={cn('flex flex-col gap-3 opacity-0 group-hover:opacity-100 transition-all duration-300', className)}>
      {/* Rating Buttons */}
      <div className="flex items-center gap-2">
        <span className="text-xs text-muted-foreground font-medium mr-1">
          {t('feedback.helpful', 'Was this helpful?')}
        </span>

        <Button
          variant="ghost"
          size="icon"
          className={cn(
            'h-8 w-8 rounded-lg transition-all duration-200',
            selectedRating === 'positive'
              ? 'bg-success/15 text-success hover:bg-success/20 scale-105 shadow-premium-sm'
              : 'hover:bg-success/10 hover:text-success hover:scale-105'
          )}
          onClick={() => handleRatingClick('positive')}
          disabled={isSubmitting}
          aria-label={t('feedback.thumbsUp', 'Thumbs up')}
        >
          <ThumbsUp
            className={cn(
              'h-4 w-4 transition-all duration-200',
              selectedRating === 'positive' && 'fill-current'
            )}
          />
        </Button>

        <Button
          variant="ghost"
          size="icon"
          className={cn(
            'h-8 w-8 rounded-lg transition-all duration-200',
            selectedRating === 'negative'
              ? 'bg-destructive/15 text-destructive hover:bg-destructive/20 scale-105 shadow-premium-sm'
              : 'hover:bg-destructive/10 hover:text-destructive hover:scale-105'
          )}
          onClick={() => handleRatingClick('negative')}
          disabled={isSubmitting}
          aria-label={t('feedback.thumbsDown', 'Thumbs down')}
        >
          <ThumbsDown
            className={cn(
              'h-4 w-4 transition-all duration-200',
              selectedRating === 'negative' && 'fill-current'
            )}
          />
        </Button>

        {selectedRating && !showCommentField && selectedRating === 'positive' && (
          <Button
            variant="ghost"
            size="sm"
            className="h-8 text-xs ml-1 hover:bg-accent/10 animate-fade-in"
            onClick={() => setShowCommentField(true)}
          >
            <MessageSquare className="h-3.5 w-3.5" />
            {t('feedback.addComment', 'Add comment')}
          </Button>
        )}
      </div>

      {/* Expandable Comment Field */}
      {showCommentField && selectedRating && (
        <div className="flex flex-col gap-2 animate-fade-in">
          <div className="relative">
            <textarea
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              placeholder={t(
                'feedback.commentPlaceholder',
                selectedRating === 'negative'
                  ? 'What could be improved?'
                  : 'What did you like? (optional)'
              )}
              className={cn(
                'w-full min-h-[80px] px-3 py-2.5 text-sm rounded-lg',
                'bg-background border-2 border-border/50',
                'focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20',
                'transition-all duration-200',
                'resize-none scrollbar-thin',
                'placeholder:text-muted-foreground/60'
              )}
              maxLength={500}
              disabled={isSubmitting}
            />
            <div className="absolute bottom-2 right-2 text-xs text-muted-foreground font-mono">
              {comment.length}/500
            </div>
          </div>

          <div className="flex items-center gap-2">
            <Button
              size="sm"
              onClick={handleSubmit}
              disabled={isSubmitting}
              className="h-8 px-4 font-medium"
            >
              {isSubmitting ? (
                <>
                  <div className="h-3 w-3 border-2 border-primary-foreground/30 border-t-primary-foreground rounded-full animate-spin" />
                  {t('feedback.submitting', 'Submitting...')}
                </>
              ) : (
                <>
                  <Send className="h-3.5 w-3.5" />
                  {t('feedback.submit', 'Submit')}
                </>
              )}
            </Button>

            <Button
              variant="ghost"
              size="sm"
              onClick={() => {
                setShowCommentField(false);
                setComment('');
              }}
              disabled={isSubmitting}
              className="h-8 px-4"
            >
              {t('feedback.cancel', 'Cancel')}
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
