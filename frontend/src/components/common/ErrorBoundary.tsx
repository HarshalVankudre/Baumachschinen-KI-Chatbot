/**
 * Error Boundary Component
 *
 * React error boundary to catch and handle errors in component tree.
 * Prevents entire app from crashing when a component throws an error.
 *
 * Features:
 * - Catches rendering errors in children
 * - Displays fallback UI
 * - Logs errors for monitoring
 * - Provides error recovery options
 */
import React, { Component } from 'react';
import type { ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

interface ErrorBoundaryProps {
  /**
   * Children components to protect
   */
  children: ReactNode;

  /**
   * Custom fallback UI (optional)
   */
  fallback?: (error: Error, resetError: () => void) => ReactNode;

  /**
   * Callback when error occurs (for logging/monitoring)
   */
  onError?: (error: Error, errorInfo: ErrorInfo) => void;

  /**
   * Whether to show detailed error in development
   */
  showDetails?: boolean;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * Error Boundary Component
 *
 * Usage:
 * ```tsx
 * <ErrorBoundary>
 *   <YourComponent />
 * </ErrorBoundary>
 * ```
 *
 * With custom fallback:
 * ```tsx
 * <ErrorBoundary fallback={(error, reset) => <CustomError error={error} onReset={reset} />}>
 *   <YourComponent />
 * </ErrorBoundary>
 * ```
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state so next render shows fallback UI
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console in development
    if (import.meta.env.DEV) {
      console.error('ErrorBoundary caught an error:', error);
      console.error('Error Info:', errorInfo);
    }

    // Update state with error info
    this.setState({
      errorInfo,
    });

    // Call custom error handler if provided
    if (this.props.onError) {
      this.props.onError(error, errorInfo);
    }
  }

  handleReset = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleReload = (): void => {
    window.location.reload();
  };

  handleGoHome = (): void => {
    window.location.href = '/';
  };

  render(): ReactNode {
    const { hasError, error, errorInfo } = this.state;
    const { children, fallback, showDetails = import.meta.env.DEV } = this.props;

    if (hasError && error) {
      // Use custom fallback if provided
      if (fallback) {
        return fallback(error, this.handleReset);
      }

      // Default error UI
      return (
        <div className="min-h-screen flex items-center justify-center p-4 bg-background">
          <Card className="max-w-2xl w-full">
            <CardHeader>
              <div className="flex items-center gap-3">
                <div className="p-3 bg-destructive/10 rounded-full">
                  <AlertTriangle className="h-6 w-6 text-destructive" />
                </div>
                <div>
                  <CardTitle>Etwas ist schief gelaufen</CardTitle>
                  <CardDescription>
                    Ein unerwarteter Fehler ist aufgetreten. Wir entschuldigen uns für die Unannehmlichkeiten.
                  </CardDescription>
                </div>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {showDetails && (
                <div className="space-y-3">
                  <div className="bg-muted p-4 rounded-lg border">
                    <p className="text-sm font-medium text-destructive mb-2">
                      Fehler:
                    </p>
                    <code className="text-xs text-muted-foreground block whitespace-pre-wrap">
                      {error.toString()}
                    </code>
                  </div>

                  {errorInfo && (
                    <details className="bg-muted p-4 rounded-lg border cursor-pointer">
                      <summary className="text-sm font-medium mb-2 select-none">
                        Stack Trace (für Entwickler)
                      </summary>
                      <code className="text-xs text-muted-foreground block whitespace-pre-wrap mt-2">
                        {errorInfo.componentStack}
                      </code>
                    </details>
                  )}
                </div>
              )}

              <div className="flex flex-wrap gap-2 pt-4">
                <Button onClick={this.handleReset} variant="default">
                  <RefreshCw className="mr-2 h-4 w-4" />
                  Erneut versuchen
                </Button>
                <Button onClick={this.handleReload} variant="outline">
                  Seite neu laden
                </Button>
                <Button onClick={this.handleGoHome} variant="ghost">
                  <Home className="mr-2 h-4 w-4" />
                  Zur Startseite
                </Button>
              </div>

              <p className="text-xs text-muted-foreground pt-4">
                Wenn das Problem weiterhin besteht, kontaktieren Sie bitte den Support.
              </p>
            </CardContent>
          </Card>
        </div>
      );
    }

    return children;
  }
}

/**
 * Functional Error Boundary Hook (for specific sections)
 *
 * Usage:
 * ```tsx
 * function MyComponent() {
 *   const { ErrorBoundary, resetError } = useErrorBoundary();
 *
 *   return (
 *     <ErrorBoundary>
 *       <Content />
 *     </ErrorBoundary>
 *   );
 * }
 * ```
 */
export function useErrorBoundary() {
  const [error, setError] = React.useState<Error | null>(null);

  const resetError = React.useCallback(() => {
    setError(null);
  }, []);

  const ErrorBoundaryWrapper = React.useCallback(
    ({ children }: { children: ReactNode }) => (
      <ErrorBoundary onError={(err) => setError(err)}>
        {children}
      </ErrorBoundary>
    ),
    []
  );

  return {
    error,
    resetError,
    ErrorBoundary: ErrorBoundaryWrapper,
  };
}

/**
 * Simple error fallback component for inline use
 */
export function SimpleErrorFallback({
  error,
  resetError,
  title = 'Fehler',
  message = 'Ein Fehler ist aufgetreten.',
}: {
  error: Error;
  resetError: () => void;
  title?: string;
  message?: string;
}) {
  return (
    <div className="p-6 border border-destructive/50 rounded-lg bg-destructive/5">
      <div className="flex items-start gap-3">
        <AlertTriangle className="h-5 w-5 text-destructive mt-0.5" />
        <div className="flex-1">
          <h3 className="font-semibold text-destructive">{title}</h3>
          <p className="text-sm text-muted-foreground mt-1">{message}</p>
          {import.meta.env.DEV && (
            <code className="text-xs text-muted-foreground block mt-2 p-2 bg-muted rounded">
              {error.toString()}
            </code>
          )}
          <Button
            size="sm"
            variant="outline"
            onClick={resetError}
            className="mt-3"
          >
            <RefreshCw className="mr-2 h-3 w-3" />
            Erneut versuchen
          </Button>
        </div>
      </div>
    </div>
  );
}
