import { useNavigate } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { ShieldAlert, Home } from 'lucide-react';

export default function ForbiddenPage() {
  const navigate = useNavigate();

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <Card className="max-w-md w-full">
        <CardHeader className="text-center space-y-4">
          <div className="mx-auto w-16 h-16 bg-destructive/10 rounded-full flex items-center justify-center">
            <ShieldAlert className="w-8 h-8 text-destructive" />
          </div>
          <CardTitle className="text-2xl">Zugriff verweigert</CardTitle>
          <CardDescription className="text-base">
            Sie haben keine Berechtigung, auf diese Seite zuzugreifen. Dieser Bereich ist nur
            für Administratoren zugänglich.
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <p className="text-sm text-muted-foreground text-center">
            Wenn Sie glauben, dass Sie Zugriff auf diese Seite haben sollten, wenden Sie sich bitte an Ihren
            Systemadministrator.
          </p>
          <Button
            onClick={() => navigate('/chat')}
            className="w-full"
          >
            <Home className="w-4 h-4 mr-2" />
            Zum Dashboard
          </Button>
        </CardContent>
      </Card>
    </div>
  );
}
