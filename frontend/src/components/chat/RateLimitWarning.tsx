import { useState, useEffect } from 'react';
import { AlertTriangle, Clock, Zap, Crown, X } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { useTranslation } from 'react-i18next';

interface RateLimitWarningProps {
  remainingQueries: number;
  maxQueries: number;
  resetTime: Date; // When the limit resets
  isFreeTier?: boolean;
  onUpgrade?: () => void;
  onDismiss?: () => void;
  className?: string;
}

export function RateLimitWarning({
  remainingQueries,
  maxQueries,
  resetTime,
  isFreeTier = false,
  onUpgrade,
  onDismiss,
  className,
}: RateLimitWarningProps) {
  const { t } = useTranslation();
  const [timeUntilReset, setTimeUntilReset] = useState('');
  const [isDismissed, setIsDismissed] = useState(false);

  const usedQueries = maxQueries - remainingQueries;
  const usagePercentage = (usedQueries / maxQueries) * 100;
  const isNearLimit = usagePercentage >= 80;
  const isAtLimit = remainingQueries === 0;

  useEffect(() => {
    const updateCountdown = () => {
      const now = new Date();
      const diff = resetTime.getTime() - now.getTime();

      if (diff <= 0) {
        setTimeUntilReset(t('rateLimit.resetting', 'Resetting...'));
        return;
      }

      const hours = Math.floor(diff / (1000 * 60 * 60));
      const minutes = Math.floor((diff % (1000 * 60 * 60)) / (1000 * 60));
      const seconds = Math.floor((diff % (1000 * 60)) / 1000);

      if (hours > 0) {
        setTimeUntilReset(`${hours}h ${minutes}m`);
      } else if (minutes > 0) {
        setTimeUntilReset(`${minutes}m ${seconds}s`);
      } else {
        setTimeUntilReset(`${seconds}s`);
      }
    };

    updateCountdown();
    const interval = setInterval(updateCountdown, 1000);

    return () => clearInterval(interval);
  }, [resetTime, t]);

  const handleDismiss = () => {
    setIsDismissed(true);
    onDismiss?.();
  };

  // Don't show if dismissed or if usage is low and not at limit
  if (isDismissed || (!isNearLimit && !isAtLimit)) {
    return null;
  }

  return (
    <div
      className={cn(
        'relative overflow-hidden rounded-xl border shadow-premium-lg animate-fade-in',
        isAtLimit
          ? 'bg-destructive/5 border-destructive/30'
          : 'bg-warning/5 border-warning/30',
        className
      )}
    >
      {/* Animated Background Gradient */}
      <div className="absolute inset-0 opacity-30">
        <div
          className={cn(
            'absolute inset-0 animate-pulse-subtle',
            isAtLimit
              ? 'bg-gradient-to-r from-destructive/10 to-transparent'
              : 'bg-gradient-to-r from-warning/10 to-transparent'
          )}
        />
      </div>

      <div className="relative p-5">
        <div className="flex items-start gap-4">
          {/* Icon */}
          <div
            className={cn(
              'flex-shrink-0 p-2.5 rounded-lg shadow-premium-sm',
              isAtLimit
                ? 'bg-destructive/20 text-destructive'
                : 'bg-warning/20 text-warning'
            )}
          >
            {isAtLimit ? (
              <AlertTriangle className="h-6 w-6" />
            ) : (
              <Zap className="h-6 w-6" />
            )}
          </div>

          {/* Content */}
          <div className="flex-1 space-y-3">
            <div className="flex items-start justify-between gap-4">
              <div>
                <h3 className="text-base font-semibold text-foreground mb-1">
                  {isAtLimit
                    ? t('rateLimit.limitReached', 'Query Limit Reached')
                    : t('rateLimit.approachingLimit', 'Approaching Query Limit')}
                </h3>
                <p className="text-sm text-muted-foreground leading-relaxed">
                  {isAtLimit
                    ? t(
                        'rateLimit.limitReachedDesc',
                        "You've used all your queries for this period. Please wait for the reset or upgrade your plan."
                      )
                    : t(
                        'rateLimit.approachingLimitDesc',
                        "You're running low on queries. Consider upgrading to continue uninterrupted access."
                      )}
                </p>
              </div>

              {/* Dismiss Button */}
              {!isAtLimit && (
                <Button
                  variant="ghost"
                  size="icon"
                  className="h-8 w-8 -mt-1 -mr-1 hover:bg-background/50"
                  onClick={handleDismiss}
                  aria-label={t('rateLimit.dismiss', 'Dismiss')}
                >
                  <X className="h-4 w-4" />
                </Button>
              )}
            </div>

            {/* Usage Bar */}
            <div className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span className="font-medium text-foreground">
                  {remainingQueries} / {maxQueries} {t('rateLimit.queriesRemaining', 'queries remaining')}
                </span>
                <span
                  className={cn(
                    'font-semibold',
                    isAtLimit ? 'text-destructive' : 'text-warning'
                  )}
                >
                  {usagePercentage.toFixed(0)}%
                </span>
              </div>

              <div className="relative h-3 bg-background/50 rounded-full overflow-hidden border border-border/50">
                <div
                  className={cn(
                    'absolute inset-y-0 left-0 rounded-full transition-all duration-700 ease-out',
                    isAtLimit
                      ? 'bg-gradient-to-r from-destructive to-destructive/80'
                      : 'bg-gradient-to-r from-warning to-warning/80'
                  )}
                  style={{ width: `${usagePercentage}%` }}
                >
                  {/* Shimmer effect */}
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
                </div>
              </div>
            </div>

            {/* Reset Timer */}
            <div className="flex items-center gap-2 text-sm">
              <Clock className="h-4 w-4 text-muted-foreground" />
              <span className="text-muted-foreground">
                {t('rateLimit.resetsIn', 'Resets in')}{' '}
                <span className="font-mono font-semibold text-foreground">
                  {timeUntilReset}
                </span>
              </span>
            </div>

            {/* Upgrade CTA (only for free tier) */}
            {isFreeTier && onUpgrade && (
              <div className="pt-3 flex items-center gap-3">
                <Button
                  onClick={onUpgrade}
                  className="bg-gradient-to-r from-accent to-accent/90 hover:shadow-premium-lg hover:-translate-y-0.5 transition-all duration-200"
                  size="sm"
                >
                  <Crown className="h-4 w-4" />
                  {t('rateLimit.upgradePlan', 'Upgrade Plan')}
                </Button>
                <p className="text-xs text-muted-foreground">
                  {t('rateLimit.unlimitedAccess', 'Get unlimited queries and priority support')}
                </p>
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
