import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { ArrowLeft, Mail, CheckCircle } from 'lucide-react';
import { authService } from '@/services/authService';

export default function ForgotPasswordPage() {
  const [email, setEmail] = useState('');
  const [loading, setLoading] = useState(false);
  const [submitted, setSubmitted] = useState(false);
  const [error, setError] = useState('');

  const validateEmail = (email: string) => {
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    return emailRegex.test(email);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    // Validate email
    if (!email.trim()) {
      setError('E-Mail-Adresse erforderlich');
      return;
    }

    if (!validateEmail(email)) {
      setError('Bitte geben Sie eine gültige E-Mail-Adresse ein');
      return;
    }

    setLoading(true);

    try {
      await authService.requestPasswordReset(email);
      setSubmitted(true);
    } catch (error: any) {
      // Generic error message for security
      console.error('Password reset error:', error);
      setError('Ein Fehler ist aufgetreten. Bitte versuchen Sie es später erneut.');
    } finally {
      setLoading(false);
    }
  };

  if (submitted) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background px-4">
        <Card className="w-full max-w-md">
          <CardHeader className="space-y-1">
            <div className="flex justify-center mb-4">
              <div className="h-12 w-12 bg-green-500 rounded-full flex items-center justify-center">
                <CheckCircle className="h-6 w-6 text-white" />
              </div>
            </div>
            <CardTitle className="text-2xl text-center">E-Mail gesendet</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <Alert>
              <Mail className="h-4 w-4" />
              <AlertDescription>
                Wenn ein Konto mit der E-Mail-Adresse <strong>{email}</strong> existiert,
                haben wir Ihnen Anweisungen zum Zurücksetzen Ihres Passworts gesendet.
              </AlertDescription>
            </Alert>
            <div className="text-sm text-muted-foreground">
              <p>Bitte überprüfen Sie Ihren Posteingang und folgen Sie den Anweisungen in der E-Mail.</p>
              <p className="mt-2">Der Link ist 1 Stunde lang gültig.</p>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-2">
            <Link to="/login" className="w-full">
              <Button variant="outline" className="w-full">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Zurück zur Anmeldung
              </Button>
            </Link>
            <button
              type="button"
              onClick={() => {
                setSubmitted(false);
                setEmail('');
              }}
              className="text-sm text-primary hover:underline"
            >
              E-Mail nicht erhalten? Erneut versuchen
            </button>
          </CardFooter>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex justify-center mb-4">
            <div className="h-12 w-12 bg-primary rounded-lg flex items-center justify-center">
              <span className="text-2xl text-primary-foreground font-bold">BC</span>
            </div>
          </div>
          <CardTitle className="text-2xl text-center">Passwort vergessen?</CardTitle>
          <CardDescription className="text-center">
            Geben Sie Ihre E-Mail-Adresse ein und wir senden Ihnen Anweisungen zum Zurücksetzen
          </CardDescription>
        </CardHeader>
        <form onSubmit={handleSubmit}>
          <CardContent className="space-y-4">
            {error && (
              <Alert variant="destructive">
                <AlertDescription>{error}</AlertDescription>
              </Alert>
            )}

            <div className="space-y-2">
              <Label htmlFor="email">E-Mail-Adresse</Label>
              <Input
                id="email"
                type="email"
                placeholder="ihre.email@beispiel.de"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoFocus
                disabled={loading}
                aria-describedby={error ? 'email-error' : undefined}
              />
              <p className="text-sm text-muted-foreground">
                Geben Sie die E-Mail-Adresse ein, die mit Ihrem Konto verknüpft ist
              </p>
            </div>
          </CardContent>
          <CardFooter className="flex flex-col space-y-4">
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Wird gesendet...' : 'Reset-Link senden'}
            </Button>
            <Link to="/login" className="w-full">
              <Button variant="outline" className="w-full">
                <ArrowLeft className="mr-2 h-4 w-4" />
                Zurück zur Anmeldung
              </Button>
            </Link>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}