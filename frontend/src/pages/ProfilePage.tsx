import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Header } from '@/components/layout/Header';
import { PasswordInput } from '@/components/shared/PasswordInput';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { useAuthStore } from '@/store/authStore';
import { authService } from '@/services/authService';
import { useToast } from '@/hooks/use-toast';

export default function ProfilePage() {
  const { user } = useAuthStore();
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const { toast } = useToast();

  const handleChangePassword = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!currentPassword || !newPassword || !confirmPassword) {
      toast({
        title: 'Validierungsfehler',
        description: 'Bitte füllen Sie alle Passwortfelder aus',
        variant: 'destructive',
      });
      return;
    }

    if (newPassword !== confirmPassword) {
      toast({
        title: 'Validierungsfehler',
        description: 'Neue Passwörter stimmen nicht überein',
        variant: 'destructive',
      });
      return;
    }

    if (newPassword.length < 12) {
      toast({
        title: 'Validierungsfehler',
        description: 'Passwort muss mindestens 12 Zeichen lang sein',
        variant: 'destructive',
      });
      return;
    }

    setLoading(true);
    try {
      await authService.changePassword(currentPassword, newPassword);
      toast({
        title: 'Erfolgreich',
        description: 'Passwort erfolgreich geändert',
      });
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error: any) {
      toast({
        title: 'Fehler',
        description: error.response?.data?.message || 'Passwort konnte nicht geändert werden',
        variant: 'destructive',
      });
    } finally {
      setLoading(false);
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background flex flex-col">
      <Header />
      <div className="flex-1 p-8">
        <div className="max-w-4xl mx-auto space-y-6">
          <h1 className="text-3xl font-bold">Benutzerprofil</h1>

        {/* Profile Information */}
        <Card>
          <CardHeader>
            <CardTitle>Profilinformationen</CardTitle>
            <CardDescription>Ihre Kontodetails</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <Label>Benutzername</Label>
                <div className="mt-2 font-medium">{user.username}</div>
              </div>
              <div>
                <Label>E-Mail</Label>
                <div className="mt-2 font-medium">{user.email}</div>
              </div>
              <div>
                <Label>Berechtigungsebene</Label>
                <div className="mt-2">
                  <StatusBadge authLevel={user.authorization_level} />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Change Password */}
        <Card>
          <CardHeader>
            <CardTitle>Passwort ändern</CardTitle>
            <CardDescription>
              Aktualisieren Sie Ihr Passwort, um Ihr Konto sicher zu halten
            </CardDescription>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleChangePassword} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="currentPassword">Aktuelles Passwort</Label>
                <PasswordInput
                  id="currentPassword"
                  value={currentPassword}
                  onChange={setCurrentPassword}
                  placeholder="Aktuelles Passwort eingeben"
                  disabled={loading}
                  autoComplete="current-password"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="newPassword">Neues Passwort</Label>
                <PasswordInput
                  id="newPassword"
                  value={newPassword}
                  onChange={setNewPassword}
                  placeholder="Neues Passwort eingeben (mind. 12 Zeichen)"
                  disabled={loading}
                  showStrengthMeter={true}
                  autoComplete="new-password"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword">Neues Passwort bestätigen</Label>
                <PasswordInput
                  id="confirmPassword"
                  value={confirmPassword}
                  onChange={setConfirmPassword}
                  placeholder="Neues Passwort erneut eingeben"
                  disabled={loading}
                  autoComplete="new-password"
                />
              </div>
              <Button type="submit" disabled={loading} variant="accent">
                {loading ? 'Wird aktualisiert...' : 'Passwort aktualisieren'}
              </Button>
            </form>
          </CardContent>
        </Card>
        </div>
      </div>
    </div>
  );
}
