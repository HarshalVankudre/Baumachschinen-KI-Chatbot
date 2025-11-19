import { useState, useEffect } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Checkbox } from '@/components/ui/checkbox';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { PasswordInput } from '@/components/shared/PasswordInput';
import { useAuth } from '@/hooks/useAuth';
import { useToast } from '@/hooks/use-toast';
import { useAuthStore } from '@/store/authStore';
import { authService } from '@/services/authService';

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const { login, loading } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  // Redirect if already authenticated on initial mount only
  useEffect(() => {
    if (isAuthenticated) {
      console.log('[LoginPage] Already authenticated on mount, redirecting to /chat');
      navigate('/chat', { replace: true });
    }
    // Only run on mount, not when isAuthenticated changes during login
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []); // Empty deps array - run only once on mount

  const validate = () => {
    const newErrors: Record<string, string> = {};

    if (!username.trim()) {
      newErrors.username = 'Benutzername oder E-Mail erforderlich';
    }

    if (!password) {
      newErrors.password = 'Passwort erforderlich';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Clear previous errors
    setErrors({});

    // Validate inputs
    if (!validate()) {
      return;
    }

    try {
      console.log('[LoginPage] Starting login attempt for user:', username);
      const response = await login(username, password);
      console.log('[LoginPage] Login response received:', response);

      // Check if we got a valid response with user data (response IS the user object)
      if (response && response.user_id) {
        console.log('[LoginPage] Login successful, user:', response);

        // Wait for Zustand persist and session cookie to be fully established
        // This ensures auth state is fully persisted to localStorage
        // and the backend session cookie is set properly
        console.log('[LoginPage] Waiting for auth state to persist and session to establish...');
        await new Promise(resolve => setTimeout(resolve, 300));

        // Verify session is working by calling /api/auth/me
        // This ensures the session cookie is properly set before navigating
        console.log('[LoginPage] Verifying session...');
        try {
          await authService.getCurrentUser();
          console.log('[LoginPage] Session verified successfully');
        } catch (sessionError) {
          console.error('[LoginPage] Session verification failed:', sessionError);
          // If session verification fails, wait a bit more and try once more
          console.log('[LoginPage] Retrying session verification after delay...');
          await new Promise(resolve => setTimeout(resolve, 200));
          try {
            await authService.getCurrentUser();
            console.log('[LoginPage] Session verified on retry');
          } catch (retryError) {
            console.error('[LoginPage] Session verification failed on retry:', retryError);
            // Session still not working - clear auth and show error
            setErrors({ general: 'Sitzung konnte nicht erstellt werden. Bitte versuchen Sie es erneut.' });
            toast({
              title: 'Sitzungsfehler',
              description: 'Ihre Sitzung konnte nicht erstellt werden. Bitte melden Sie sich erneut an.',
              variant: 'destructive',
            });
            return; // Don't navigate to chat
          }
        }

        // Show success message
        toast({
          title: 'Erfolgreich',
          description: 'Erfolgreich angemeldet',
        });

        console.log('[LoginPage] Navigating to /chat');
        navigate('/chat', { replace: true });
      } else {
        // This shouldn't happen with a 200 response, but handle it just in case
        console.error('[LoginPage] Login response missing user data:', response);
        setErrors({ general: 'Anmeldung fehlgeschlagen. Ungültige Serverantwort.' });
        toast({
          title: 'Anmeldung fehlgeschlagen',
          description: 'Ungültige Serverantwort',
          variant: 'destructive',
        });
      }
    } catch (error: any) {
      console.error('[LoginPage] Login error:', error);

      // Handle different error scenarios
      const status = error.response?.status;
      const message = error.response?.data?.message;

      let errorMessage = '';

      if (status === 401) {
        errorMessage = 'Ungültige Anmeldedaten';
      } else if (status === 403) {
        if (message?.includes('not verified')) {
          errorMessage = 'Bitte verifizieren Sie Ihre E-Mail-Adresse';
        } else if (message?.includes('pending approval')) {
          errorMessage = 'Ihr Konto wartet auf Genehmigung';
        } else {
          errorMessage = message || 'Zugriff verweigert';
        }
      } else if (status === 500) {
        errorMessage = 'Serverfehler. Bitte versuchen Sie es später erneut.';
      } else {
        errorMessage = message || 'Anmeldung fehlgeschlagen';
      }

      setErrors({ general: errorMessage });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-subtle px-4 py-8">
      <Card className="w-full max-w-md shadow-premium-xl animate-fade-in">
        <CardHeader className="space-y-3">
          <div className="flex justify-center mb-2">
            <div className="h-16 w-16 bg-gradient-primary rounded-2xl flex items-center justify-center shadow-premium-md hover:shadow-premium-lg transition-all duration-300 hover:scale-105">
              <span className="text-3xl text-primary-foreground font-bold">BK</span>
            </div>
          </div>
          <CardTitle className="text-3xl text-center">Baumaschinen-KI</CardTitle>
          <CardDescription className="text-center text-base">
            Melden Sie sich an, um auf den Chatbot zuzugreifen
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-5">
            {errors.general && (
              <div className="p-4 rounded-xl bg-destructive/10 border-2 border-destructive/30 text-destructive text-sm font-medium shadow-premium-xs animate-fade-in">
                {errors.general}
              </div>
            )}

            <div className="space-y-2.5">
              <Label htmlFor="username" className="text-sm font-semibold">E-Mail oder Benutzername</Label>
              <Input
                id="username"
                type="text"
                placeholder="ihre@firma.de oder benutzername"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoFocus
                disabled={loading}
                aria-invalid={!!errors.username}
                aria-describedby={errors.username ? 'username-error' : undefined}
                className="h-11 rounded-xl border-2"
              />
              {errors.username && (
                <p id="username-error" className="text-sm text-destructive font-medium animate-fade-in">
                  {errors.username}
                </p>
              )}
            </div>

            <div className="space-y-2.5">
              <Label htmlFor="password" className="text-sm font-semibold">Passwort</Label>
              <PasswordInput
                id="password"
                value={password}
                onChange={setPassword}
                placeholder="Geben Sie Ihr Passwort ein"
                disabled={loading}
                autoComplete="current-password"
              />
              {errors.password && (
                <p id="password-error" className="text-sm text-destructive font-medium animate-fade-in">
                  {errors.password}
                </p>
              )}
            </div>

            <div className="flex items-center space-x-2.5">
              <Checkbox
                id="remember"
                checked={rememberMe}
                onCheckedChange={(checked) => setRememberMe(checked as boolean)}
              />
              <label htmlFor="remember" className="text-sm text-muted-foreground cursor-pointer font-medium">
                Angemeldet bleiben
              </label>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-5">
            <Button type="submit" className="w-full h-12 text-base font-semibold shadow-premium-md hover:shadow-premium-lg" disabled={loading} variant="accent">
              {loading ? 'Wird angemeldet...' : 'Anmelden'}
            </Button>
            <div className="flex flex-col space-y-3 text-sm text-center">
              <Link to="/forgot-password" className="text-primary hover:text-primary/80 font-medium transition-colors">
                Passwort vergessen?
              </Link>
              <div className="text-muted-foreground">
                Noch kein Konto?{' '}
                <Link to="/register" className="text-primary hover:text-primary/80 font-semibold transition-colors">
                  Registrieren
                </Link>
              </div>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
