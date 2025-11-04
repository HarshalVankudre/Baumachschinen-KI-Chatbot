import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import { translateAuthLevel, translateProcessingStatus } from '@/utils/translations';

type StatusVariant = 'success' | 'warning' | 'error' | 'info' | 'processing';
type AuthLevel = 'regular' | 'superuser' | 'admin';
type ProcessingStatus = 'uploading' | 'processing' | 'completed' | 'failed';

interface StatusBadgeProps {
  variant?: StatusVariant;
  authLevel?: AuthLevel;
  processingStatus?: ProcessingStatus;
  children?: React.ReactNode;
  className?: string;
}

export function StatusBadge({
  variant,
  authLevel,
  processingStatus,
  children,
  className,
}: StatusBadgeProps) {
  // Determine the variant and text based on props
  let badgeVariant: StatusVariant = variant || 'info';
  let text = children;

  if (authLevel) {
    text = translateAuthLevel(authLevel);
    switch (authLevel) {
      case 'admin':
        badgeVariant = 'error';
        break;
      case 'superuser':
        badgeVariant = 'warning';
        break;
      case 'regular':
        badgeVariant = 'info';
        break;
    }
  }

  if (processingStatus) {
    text = translateProcessingStatus(processingStatus);
    switch (processingStatus) {
      case 'completed':
        badgeVariant = 'success';
        break;
      case 'failed':
        badgeVariant = 'error';
        break;
      case 'processing':
      case 'uploading':
        badgeVariant = 'processing';
        break;
    }
  }

  const variantStyles = {
    success: 'bg-green-100 text-green-800 border-green-200 hover:bg-green-100',
    warning: 'bg-yellow-100 text-yellow-800 border-yellow-200 hover:bg-yellow-100',
    error: 'bg-red-100 text-red-800 border-red-200 hover:bg-red-100',
    info: 'bg-blue-100 text-blue-800 border-blue-200 hover:bg-blue-100',
    processing: 'bg-purple-100 text-purple-800 border-purple-200 hover:bg-purple-100',
  };

  return (
    <Badge
      variant="outline"
      className={cn(
        'font-medium',
        variantStyles[badgeVariant],
        processingStatus === 'processing' && 'animate-pulse',
        className
      )}
    >
      {text}
    </Badge>
  );
}
