import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Checkbox } from '@/components/ui/checkbox';
import { PasswordInput } from '@/components/shared/PasswordInput';
import { useAuth } from '@/hooks/useAuth';
import { useToast } from '@/hooks/use-toast';

export default function RegisterPage() {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [agreedToTerms, setAgreedToTerms] = useState(false);
  const [errors, setErrors] = useState<Record<string, string>>({});

  const { register, loading } = useAuth();
  const { toast } = useToast();
  const navigate = useNavigate();

  const validateEmail = (email: string): boolean => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!email) {
      newErrors.email = 'E-Mail erforderlich';
    } else if (!validateEmail(email)) {
      newErrors.email = 'Bitte geben Sie eine gültige E-Mail-Adresse ein';
    }

    if (!username) {
      newErrors.username = 'Benutzername erforderlich';
    } else if (username.length < 3) {
      newErrors.username = 'Benutzername muss mindestens 3 Zeichen lang sein';
    }

    if (!password) {
      newErrors.password = 'Passwort erforderlich';
    } else if (password.length < 12) {
      newErrors.password = 'Passwort muss mindestens 12 Zeichen lang sein';
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = 'Bitte bestätigen Sie Ihr Passwort';
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwörter stimmen nicht überein';
    }

    if (!agreedToTerms) {
      newErrors.terms = 'Sie müssen den Nutzungsbedingungen zustimmen';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    // Clear previous errors
    setErrors({});

    if (!validateForm()) {
      return;
    }

    try {
      await register(email, username, password, confirmPassword);
      toast({
        title: 'Erfolgreich',
        description: 'Konto erfolgreich erstellt. Bitte überprüfen Sie Ihre E-Mail, um Ihr Konto zu verifizieren.',
      });
      navigate('/check-email');
    } catch (error: any) {
      const status = error.response?.status;
      const message = error.response?.data?.message;

      if (status === 409) {
        // Duplicate username or email
        if (message?.toLowerCase().includes('username')) {
          setErrors({ username: 'Benutzername bereits vergeben. Bitte wählen Sie einen anderen.' });
        } else if (message?.toLowerCase().includes('email')) {
          setErrors({ email: 'E-Mail bereits registriert. Bitte verwenden Sie eine andere oder melden Sie sich an.' });
        } else {
          setErrors({ general: message || 'Benutzername oder E-Mail bereits vergeben' });
        }
      } else if (status === 400) {
        // Validation errors from backend
        setErrors({ general: message || 'Ungültige Registrierungsdaten. Bitte überprüfen Sie Ihre Eingaben.' });
      } else if (status === 500) {
        setErrors({ general: 'Serverfehler. Bitte versuchen Sie es später erneut.' });
      } else {
        setErrors({ general: message || 'Ein unerwarteter Fehler ist bei der Registrierung aufgetreten' });
      }

      toast({
        title: 'Registrierung fehlgeschlagen',
        description: message || 'Ein Fehler ist bei der Registrierung aufgetreten',
        variant: 'destructive',
      });
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4 py-8">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <CardTitle className="text-2xl text-center">Konto erstellen</CardTitle>
          <CardDescription className="text-center">
            Registrieren Sie sich, um mit der Baumaschinen-KI zu starten
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
              <Label htmlFor="email">E-Mail</Label>
              <Input
                id="email"
                type="email"
                placeholder="ihre@firma.de"
                value={email}
                onChange={(e) => {
                  setEmail(e.target.value);
                  setErrors((prev) => ({ ...prev, email: '' }));
                }}
                autoFocus
                disabled={loading}
                className={errors.email ? 'border-destructive' : ''}
              />
              {errors.email && (
                <p className="text-sm text-destructive">{errors.email}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="username">Benutzername</Label>
              <Input
                id="username"
                type="text"
                placeholder="Wählen Sie einen Benutzernamen (mind. 3 Zeichen)"
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  setErrors((prev) => ({ ...prev, username: '' }));
                }}
                disabled={loading}
                className={errors.username ? 'border-destructive' : ''}
              />
              {errors.username && (
                <p className="text-sm text-destructive">{errors.username}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Passwort</Label>
              <PasswordInput
                id="password"
                value={password}
                onChange={(value) => {
                  setPassword(value);
                  setErrors((prev) => ({ ...prev, password: '' }));
                }}
                placeholder="Mind. 12 Zeichen"
                disabled={loading}
                showStrengthMeter={true}
                autoComplete="new-password"
              />
              {errors.password && (
                <p className="text-sm text-destructive">{errors.password}</p>
              )}
            </div>
            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Passwort bestätigen</Label>
              <PasswordInput
                id="confirmPassword"
                value={confirmPassword}
                onChange={(value) => {
                  setConfirmPassword(value);
                  setErrors((prev) => ({ ...prev, confirmPassword: '' }));
                }}
                placeholder="Geben Sie Ihr Passwort erneut ein"
                disabled={loading}
                autoComplete="new-password"
              />
              {errors.confirmPassword && (
                <p className="text-sm text-destructive">{errors.confirmPassword}</p>
              )}
            </div>
            <div className="space-y-2">
              <div className="flex items-start space-x-2">
                <Checkbox
                  id="terms"
                  checked={agreedToTerms}
                  onCheckedChange={(checked) => {
                    setAgreedToTerms(checked as boolean);
                    setErrors((prev) => ({ ...prev, terms: '' }));
                  }}
                  disabled={loading}
                />
                <label htmlFor="terms" className="text-sm text-muted-foreground cursor-pointer leading-tight">
                  Ich stimme den <Link to="/terms" className="text-primary hover:underline">Nutzungsbedingungen</Link> und der <Link to="/privacy" className="text-primary hover:underline">Datenschutzerklärung</Link> zu
                </label>
              </div>
              {errors.terms && (
                <p className="text-sm text-destructive">{errors.terms}</p>
              )}
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Konto wird erstellt...' : 'Konto erstellen'}
            </Button>
            <div className="text-sm text-center text-muted-foreground">
              Bereits ein Konto?{' '}
              <Link to="/login" className="text-primary hover:underline">
                Anmelden
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}
