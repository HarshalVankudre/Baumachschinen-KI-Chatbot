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

export default function LoginPage() {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [rememberMe, setRememberMe] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const { login, loading } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();
  const { isAuthenticated } = useAuthStore();

  // Redirect if already authenticated
  useEffect(() => {
    if (isAuthenticated) {
      console.log('[LoginPage] Already authenticated, redirecting to /chat');
      navigate('/chat', { replace: true });
    }
  }, [isAuthenticated, navigate]);

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

        // Show success message
        toast({
          title: 'Erfolgreich',
          description: 'Erfolgreich angemeldet',
        });

        // Navigate immediately after successful login
        // Don't wait for state updates - the auth store will handle that
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

      if (status === 401) {
        setErrors({ general: 'Ungültige Anmeldedaten. Bitte überprüfen Sie Ihren Benutzernamen und Ihr Passwort.' });
        toast({
          title: 'Anmeldung fehlgeschlagen',
          description: 'Ungültige Anmeldedaten',
          variant: 'destructive',
        });
      } else if (status === 403) {
        const forbiddenMessage = message || 'Konto nicht genehmigt';
        if (forbiddenMessage.includes('not verified')) {
          setErrors({ general: 'Bitte verifizieren Sie Ihre E-Mail-Adresse vor der Anmeldung.' });
        } else if (forbiddenMessage.includes('pending approval')) {
          setErrors({ general: 'Ihr Konto wartet auf Admin-Genehmigung. Sie werden benachrichtigt, sobald es genehmigt wurde.' });
        } else {
          setErrors({ general: forbiddenMessage });
        }
        toast({
          title: 'Zugriff verweigert',
          description: forbiddenMessage,
          variant: 'destructive',
        });
      } else if (status === 500) {
        setErrors({ general: 'Serverfehler. Bitte versuchen Sie es später erneut.' });
        toast({
          title: 'Serverfehler',
          description: 'Etwas ist schiefgelaufen. Bitte versuchen Sie es später erneut.',
          variant: 'destructive',
        });
      } else {
        setErrors({ general: message || 'Anmeldung fehlgeschlagen. Bitte versuchen Sie es erneut.' });
        toast({
          title: 'Anmeldung fehlgeschlagen',
          description: message || 'Ein unerwarteter Fehler ist aufgetreten',
          variant: 'destructive',
        });
      }
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex justify-center mb-4">
            <div className="h-12 w-12 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-2xl text-primary-foreground font-bold">BC</span>
            </div>
          </div>
          <CardTitle className="text-2xl text-center">Baumaschinen-KI</CardTitle>
          <CardDescription className="text-center">
            Melden Sie sich an, um auf den Chatbot zuzugreifen
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {errors.general && (
              <div className="p-3 rounded-md bg-destructive/10 border border-destructive/20 text-destructive text-sm">
                {errors.general}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="username">Benutzername oder E-Mail</Label>
              <Input
                id="username"
                type="text"
                placeholder="Geben Sie Ihren Benutzernamen oder E-Mail ein"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                autoFocus
                disabled={loading}
                aria-invalid={!!errors.username}
                aria-describedby={errors.username ? 'username-error' : undefined}
              />
              {errors.username && (
                <p id="username-error" className="text-sm text-destructive">
                  {errors.username}
                </p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Passwort</Label>
              <PasswordInput
                id="password"
                value={password}
                onChange={setPassword}
                placeholder="Geben Sie Ihr Passwort ein"
                disabled={loading}
                autoComplete="current-password"
              />
              {errors.password && (
                <p id="password-error" className="text-sm text-destructive">
                  {errors.password}
                </p>
              )}
            </div>

            <div className="flex items-center space-x-2">
              <Checkbox
                id="remember"
                checked={rememberMe}
                onCheckedChange={(checked) => setRememberMe(checked as boolean)}
              />
              <label htmlFor="remember" className="text-sm text-muted-foreground cursor-pointer">
                Angemeldet bleiben
              </label>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Wird angemeldet...' : 'Anmelden'}
            </Button>
            <div className="flex flex-col space-y-2 text-sm text-center">
              <Link to="/forgot-password" className="text-primary hover:underline">
                Passwort vergessen?
              </Link>
              <div className="text-muted-foreground">
                Noch kein Konto?{' '}
                <Link to="/register" className="text-primary hover:underline">
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
