import { useState, useEffect } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { PasswordInput } from '@/components/shared/PasswordInput';
import { CheckCircle, XCircle, AlertTriangle, ArrowLeft } from 'lucide-react';
import { authService } from '@/services/authService';
import { useToast } from '@/hooks/use-toast';

interface PasswordStrength {
  score: number;
  feedback: string[];
  color: string;
}

export default function ResetPasswordPage() {
  const { token } = useParams<{ token: string }>();
  const navigate = useNavigate();
  const { toast } = useToast();

  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [verifying, setVerifying] = useState(true);
  const [tokenValid, setTokenValid] = useState(false);
  const [tokenError, setTokenError] = useState('');
  const [errors, setErrors] = useState<Record<string, string>>({});
  const [passwordStrength, setPasswordStrength] = useState<PasswordStrength>({
    score: 0,
    feedback: [],
    color: 'bg-gray-300'
  });

  // Verify token on mount
  useEffect(() => {
    const verifyToken = async () => {
      if (!token) {
        setTokenError('Kein Token gefunden');
        setVerifying(false);
        return;
      }

      try {
        await authService.verifyResetToken(token);
        setTokenValid(true);
      } catch (error: any) {
        const message = error.response?.data?.detail || 'Ungültiger oder abgelaufener Reset-Link';
        setTokenError(message);
      } finally {
        setVerifying(false);
      }
    };

    verifyToken();
  }, [token]);

  // Calculate password strength
  useEffect(() => {
    if (!password) {
      setPasswordStrength({ score: 0, feedback: [], color: 'bg-gray-300' });
      return;
    }

    const feedback: string[] = [];
    let score = 0;

    // Length check
    if (password.length >= 12) {
      score += 25;
    } else {
      feedback.push('Mindestens 12 Zeichen erforderlich');
    }

    // Uppercase check
    if (/[A-Z]/.test(password)) {
      score += 25;
    } else {
      feedback.push('Mindestens ein Großbuchstabe erforderlich');
    }

    // Lowercase check
    if (/[a-z]/.test(password)) {
      score += 25;
    } else {
      feedback.push('Mindestens ein Kleinbuchstabe erforderlich');
    }

    // Number check
    if (/\d/.test(password)) {
      score += 12.5;
    } else {
      feedback.push('Mindestens eine Zahl erforderlich');
    }

    // Special character check
    if (/[!@#$%^&*()_+\-=[\]{}|;:,.<>?]/.test(password)) {
      score += 12.5;
    } else {
      feedback.push('Mindestens ein Sonderzeichen erforderlich');
    }

    let color = 'bg-red-500';
    if (score >= 100) {
      color = 'bg-green-500';
    } else if (score >= 75) {
      color = 'bg-yellow-500';
    } else if (score >= 50) {
      color = 'bg-orange-500';
    }

    setPasswordStrength({ score, feedback, color });
  }, [password]);

  const validate = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!password) {
      newErrors.password = 'Passwort erforderlich';
    } else if (passwordStrength.score < 100) {
      newErrors.password = 'Passwort erfüllt nicht alle Anforderungen';
    }

    if (!confirmPassword) {
      newErrors.confirmPassword = 'Passwortbestätigung erforderlich';
    } else if (password !== confirmPassword) {
      newErrors.confirmPassword = 'Passwörter stimmen nicht überein';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validate() || !token) {
      return;
    }

    setLoading(true);
    setErrors({});

    try {
      await authService.resetPassword(token, password, confirmPassword);

      toast({
        title: 'Passwort zurückgesetzt',
        description: 'Ihr Passwort wurde erfolgreich geändert. Sie werden zur Anmeldung weitergeleitet.',
      });

      // Redirect to login after 2 seconds
      setTimeout(() => {
        navigate('/login');
      }, 2000);
    } catch (error: any) {
      const message = error.response?.data?.detail || 'Fehler beim Zurücksetzen des Passworts';
      setErrors({ general: message });

      toast({
        title: 'Fehler',
        description: message,
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  // Loading state while verifying token
  if (verifying) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="text-center">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto"></div>
              <p className="mt-4 text-muted-foreground">Token wird überprüft...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  // Invalid token state
  if (!tokenValid) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1">
            <div className="flex justify-center mb-4">
              <div className="h-12 w-12 bg-red-500 rounded-full flex items-center justify-center">
                <XCircle className="h-6 w-6 text-white" />
              </div>
            </div>
            <CardTitle className="text-2xl text-center">Ungültiger Link</CardTitle>
          </CardHeader>
          <CardContent>
            <Alert variant="destructive">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription>{tokenError}</AlertDescription>
            </Alert>
            <p className="mt-4 text-sm text-muted-foreground text-center">
              Der Reset-Link ist ungültig oder abgelaufen. Bitte fordern Sie einen neuen Link an.
            </p>
          </CardContent>
          <CardFooter className="flex flex-col space-y-2">
            <Link to="/forgot-password" className="w-full">
              <Button className="w-full">Neuen Link anfordern</Button>
            </Link>
            <Link to="/login" className="w-full">
              <Button variant="outline" className="w-full">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Zurück zur Anmeldung
              </Button>
            </Link>
          </CardFooter>
        </Card>
      </div>
    );
  }

  // Valid token - show reset form
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex justify-center mb-4">
            <div className="h-12 w-12 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-2xl text-primary-foreground font-bold">BC</span>
            </div>
          </div>
          <CardTitle className="text-2xl text-center">Neues Passwort festlegen</CardTitle>
          <CardDescription className="text-center">
            Geben Sie Ihr neues Passwort ein
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {errors.general && (
              <Alert variant="destructive">
                <AlertDescription>{errors.general}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="password">Neues Passwort</Label>
              <PasswordInput
                id="password"
                value={password}
                onChange={setPassword}
                placeholder="Neues Passwort eingeben"
                disabled={loading}
                autoComplete="new-password"
              />
              {errors.password && (
                <p className="text-sm text-destructive">{errors.password}</p>
              )}

              {password && (
                <div className="space-y-2">
                  <div className="flex justify-between text-xs">
                    <span>Passwortstärke</span>
                    <span>{passwordStrength.score}%</span>
                  </div>
                  <Progress value={passwordStrength.score} className={passwordStrength.color} />

                  {passwordStrength.feedback.length > 0 && (
                    <ul className="text-xs text-muted-foreground space-y-1">
                      {passwordStrength.feedback.map((item, index) => (
                        <li key={index} className="flex items-center gap-1">
                          <XCircle className="h-3 w-3 text-red-500" />
                          {item}
                        </li>
                      ))}
                    </ul>
                  )}

                  {passwordStrength.score === 100 && (
                    <p className="text-xs text-green-600 flex items-center gap-1">
                      <CheckCircle className="h-3 w-3" />
                      Starkes Passwort
                    </p>
                  )}
                </div>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="confirmPassword">Passwort bestätigen</Label>
              <PasswordInput
                id="confirmPassword"
                value={confirmPassword}
                onChange={setConfirmPassword}
                placeholder="Passwort erneut eingeben"
                disabled={loading}
                autoComplete="new-password"
              />
              {errors.confirmPassword && (
                <p className="text-sm text-destructive">{errors.confirmPassword}</p>
              )}

              {confirmPassword && password && (
                <p className={`text-xs flex items-center gap-1 ${
                  password === confirmPassword ? 'text-green-600' : 'text-red-600'
                }`}>
                  {password === confirmPassword ? (
                    <>
                      <CheckCircle className="h-3 w-3" />
                      Passwörter stimmen überein
                    </>
                  ) : (
                    <>
                      <XCircle className="h-3 w-3" />
                      Passwörter stimmen nicht überein
                    </>
                  )}
                </p>
              )}
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button
              type="submit"
              className="w-full"
              disabled={loading || passwordStrength.score < 100}
            >
              {loading ? 'Wird zurückgesetzt...' : 'Passwort zurücksetzen'}
            </Button>
            <Link to="/login" className="text-sm text-primary hover:underline text-center">
              Zurück zur Anmeldung
            </Link>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}