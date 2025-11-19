import { Component, type ErrorInfo, type ReactNode } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { AlertTriangle, RefreshCcw, Home } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * ErrorBoundary Component
 *
 * Catches JavaScript errors anywhere in the child component tree.
 * Features:
 * - Logs error details to console (or external service)
 * - Shows user-friendly error message
 * - Provides retry and go home buttons
 * - Shows error stack in development mode
 * - Follows industrial design theme
 */
export class ErrorBoundary extends Component<Props, State> {
  constructor(props: Props) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    // Update state so the next render will show the fallback UI
    return {
      hasError: true,
      error,
      errorInfo: null,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    // Log error to console or external error tracking service
    console.error('ErrorBoundary caught an error:', error, errorInfo);

    // You can integrate with Sentry or other error tracking services here
    // Example: Sentry.captureException(error, { extra: errorInfo });

    this.setState({
      error,
      errorInfo,
    });
  }

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  handleGoHome = () => {
    window.location.href = '/';
  };

  render() {
    if (this.state.hasError) {
      // Custom fallback UI provided
      if (this.props.fallback) {
        return this.props.fallback;
      }

      // Default fallback UI
      return (
        <div className="min-h-screen flex items-center justify-center bg-background px-4">
          <Card className="w-full max-w-2xl">
            <CardHeader className="space-y-1">
              <div className="flex justify-center mb-4">
                <div className="h-16 w-16 bg-destructive/10 rounded-full flex items-center justify-center">
                  <AlertTriangle className="h-8 w-8 text-destructive" />
                </div>
              </div>
              <CardTitle className="text-2xl text-center">Etwas ist schiefgelaufen</CardTitle>
              <CardDescription className="text-center">
                Wir sind auf einen unerwarteten Fehler gestoßen. Der Fehler wurde protokolliert und wir werden ihn untersuchen.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="bg-muted p-4 rounded-md">
                <p className="text-sm font-medium mb-2">Fehlerdetails:</p>
                <p className="text-sm text-muted-foreground font-mono">
                  {this.state.error?.message || 'Unbekannter Fehler'}
                </p>
              </div>

              {/* Show stack trace only in development */}
              {import.meta.env.DEV && this.state.errorInfo && (
                <details className="text-xs bg-muted p-4 rounded-md">
                  <summary className="cursor-pointer font-medium mb-2">
                    Stack Trace (nur Entwicklung)
                  </summary>
                  <pre className="whitespace-pre-wrap text-muted-foreground mt-2 overflow-auto max-h-60">
                    {this.state.errorInfo.componentStack}
                  </pre>
                </details>
              )}

              <div className="bg-blue-50 dark:bg-blue-950 border border-blue-200 dark:border-blue-800 rounded-md p-4">
                <p className="text-sm text-blue-900 dark:text-blue-100">
                  <strong>Was können Sie tun?</strong>
                </p>
                <ul className="list-disc list-inside text-sm text-blue-800 dark:text-blue-200 mt-2 space-y-1">
                  <li>Versuchen Sie, die Seite zu aktualisieren</li>
                  <li>Gehen Sie zurück zur Startseite und versuchen Sie es erneut</li>
                  <li>Wenn das Problem weiterhin besteht, kontaktieren Sie den Support</li>
                </ul>
              </div>
            </CardContent>
            <CardFooter className="flex gap-3 justify-center">
              <Button variant="outline" onClick={this.handleReset} className="flex items-center gap-2">
                <RefreshCcw className="h-4 w-4" />
                Erneut versuchen
              </Button>
              <Button onClick={this.handleGoHome} className="flex items-center gap-2">
                <Home className="h-4 w-4" />
                Zur Startseite
              </Button>
            </CardFooter>
          </Card>
        </div>
      );
    }

    return this.props.children;
  }
}
