import { Button } from '@/components/ui/button';
import type { LucideIcon } from 'lucide-react';
import { cn } from '@/lib/utils';

interface EmptyStateProps {
  icon: LucideIcon;
  title: string;
  message: string;
  actionLabel?: string;
  onAction?: () => void;
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  message,
  actionLabel,
  onAction,
  className,
}: EmptyStateProps) {
  return (
    <div
      className={cn(
        'flex flex-col items-center justify-center p-12 text-center animate-fade-in',
        className
      )}
      role="status"
      aria-live="polite"
    >
      <div className="rounded-2xl bg-gradient-subtle border border-border/50 p-8 mb-6 shadow-premium-sm">
        <Icon className="h-14 w-14 text-primary/70" aria-hidden="true" />
      </div>
      <h3 className="text-xl font-bold mb-3 tracking-tight">{title}</h3>
      <p className="text-muted-foreground mb-8 max-w-md leading-relaxed">{message}</p>
      {actionLabel && onAction && (
        <Button onClick={onAction} variant="accent" size="lg" className="shadow-premium-md">
          {actionLabel}
        </Button>
      )}
    </div>
  );
}
