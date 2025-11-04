import { Link } from 'react-router-dom';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';

export default function CheckEmailPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background px-4">
      <Card className="w-full max-w-md">
        <CardHeader className="space-y-1">
          <div className="flex justify-center mb-4">
            <div className="h-16 w-16 bg-accent rounded-full flex items-center justify-center">
              <svg className="h-8 w-8 text-accent-foreground" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>
          </div>
          <CardTitle className="text-2xl text-center">Überprüfen Sie Ihre E-Mail</CardTitle>
          <CardDescription className="text-center">
            Wir haben Ihnen einen Verifizierungslink gesendet
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-center text-muted-foreground">
            Bitte überprüfen Sie Ihren Posteingang und klicken Sie auf den Verifizierungslink, um Ihre Registrierung abzuschließen.
            Nach der Verifizierung muss ein Administrator Ihr Konto genehmigen, bevor Sie sich anmelden können.
          </p>
          <div className="bg-muted p-4 rounded-md">
            <p className="text-sm text-center">
              <strong>Hinweis:</strong> Der Verifizierungslink läuft in 24 Stunden ab
            </p>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col space-y-2">
          <Button variant="outline" className="w-full" asChild>
            <Link to="/login">Zurück zur Anmeldung</Link>
          </Button>
          <p className="text-xs text-center text-muted-foreground">
            E-Mail nicht erhalten? Überprüfen Sie Ihren Spam-Ordner oder kontaktieren Sie den Support.
          </p>
        </CardFooter>
      </Card>
    </div>
  );
}
