import { useEffect, useState } from 'react';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { LoadingSpinner } from '@/components/shared/LoadingSpinner';
import { CheckCircle2, XCircle, Mail } from 'lucide-react';
import { authService } from '@/services/authService';

export default function EmailVerificationPage() {
  const [searchParams] = useSearchParams();
  const token = searchParams.get('token');
  const navigate = useNavigate();
  const [status, setStatus] = useState<'loading' | 'success' | 'error' | 'already-verified'>('loading');
  const [message, setMessage] = useState('');

  useEffect(() => {
    const verifyEmail = async () => {
      if (!token) {
        setStatus('error');
        setMessage('Ungültiger Verifizierungslink');
        return;
      }

      try {
        const response = await authService.verifyEmail(token);

        setStatus('success');
        setMessage(response.message || 'E-Mail erfolgreich verifiziert. Ihr Konto wartet auf Admin-Genehmigung.');
      } catch (error: any) {
        if (error.response?.status === 409) {
          setStatus('already-verified');
          setMessage('Diese E-Mail wurde bereits verifiziert.');
        } else if (error.response?.status === 400) {
          setStatus('error');
          setMessage('Ungültiges oder abgelaufenes Verifizierungs-Token.');
        } else {
          setStatus('error');
          setMessage(error.response?.data?.message || 'Verifizierung fehlgeschlagen. Bitte versuchen Sie es erneut.');
        }
      }
    };

    verifyEmail();
  }, [token]);

  const getIcon = () => {
    switch (status) {
      case 'loading':
        return <LoadingSpinner size="lg" />;
      case 'success':
      case 'already-verified':
        return <CheckCircle2 className="h-16 w-16 text-green-500" />;
      case 'error':
        return <XCircle className="h-16 w-16 text-destructive" />;
      default:
        return <Mail className="h-16 w-16 text-muted-foreground" />;
    }
  };

  const getTitle = () => {
    switch (status) {
      case 'loading':
        return 'Ihre E-Mail wird verifiziert';
      case 'success':
        return 'E-Mail verifiziert!';
      case 'already-verified':
        return 'Bereits verifiziert';
      case 'error':
        return 'Verifizierung fehlgeschlagen';
      default:
        return 'E-Mail-Verifizierung';
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
            E-Mail-Verifizierung
          </CardDescription>
        </CardHeader>
        <CardContent className="flex flex-col items-center text-center space-y-4 py-8">
          {getIcon()}
          <h3 className="text-xl font-semibold">{getTitle()}</h3>
          <p className="text-muted-foreground">
            {status === 'loading' && 'Bitte warten Sie, während wir Ihre E-Mail-Adresse verifizieren...'}
            {status === 'success' && message}
            {status === 'already-verified' && 'Ihre E-Mail wurde bereits verifiziert. Bitte warten Sie auf die Admin-Genehmigung.'}
            {status === 'error' && message}
          </p>
          {status === 'success' && (
            <div className="bg-muted p-4 rounded-lg text-sm">
              <p className="font-medium mb-2">Wie geht es weiter?</p>
              <ol className="text-left space-y-1">
                <li>1. Ein Administrator wird Ihr Konto überprüfen</li>
                <li>2. Sie erhalten eine E-Mail, sobald es genehmigt wurde</li>
                <li>3. Dann können Sie sich anmelden und mit dem Chatten beginnen</li>
              </ol>
            </div>
          )}
        </CardContent>
        <CardFooter className="flex justify-center">
          {status !== 'loading' && (
            <Button onClick={() => navigate('/login')} className="w-full">
              Zurück zur Anmeldung
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
