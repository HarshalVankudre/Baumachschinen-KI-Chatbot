import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import { useAuth } from '@/hooks/useAuth';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { StatusBadge } from '@/components/shared/StatusBadge';
import { useToast } from '@/hooks/use-toast';
import { User, LogOut, Building2, Shield, MessageSquare } from 'lucide-react';

interface HeaderProps {
  showSidebarToggle?: boolean;
  onToggleSidebar?: () => void;
}

/**
 * Header Component
 *
 * App header with logo, user profile dropdown, and logout functionality.
 * Features:
 * - Building Machinery AI branding
 * - User profile dropdown with avatar
 * - Authorization level badge
 * - Logout functionality with state cleanup
 * - Navigation to profile and settings
 */
export function Header({ showSidebarToggle: _showSidebarToggle, onToggleSidebar: _onToggleSidebar }: HeaderProps) {
  const navigate = useNavigate();
  const { user } = useAuthStore();
  const { logout } = useAuth();
  const { toast } = useToast();

  const handleLogout = async () => {
    try {
      await logout();
      toast({
        title: 'Abgemeldet',
        description: 'Sie wurden erfolgreich abgemeldet',
      });
      navigate('/login');
    } catch (error) {
      toast({
        title: 'Fehler',
        description: 'Abmeldung fehlgeschlagen. Bitte versuchen Sie es erneut.',
        variant: 'destructive',
      });
    }
  };

  const getUserInitials = () => {
    if (!user?.username) return 'U';
    return user.username.substring(0, 2).toUpperCase();
  };

  return (
    <header className="border-b bg-background">
      <div className="flex h-16 items-center px-4 gap-4">
        {/* Logo and Branding */}
        <div className="flex items-center gap-3">
          <div className="h-10 w-10 bg-primary rounded-lg flex items-center justify-center">
            <Building2 className="h-6 w-6 text-primary-foreground" />
          </div>
          <div className="hidden sm:block">
            <h1 className="text-lg font-semibold text-foreground">
              Baumaschinen-KI
            </h1>
            <p className="text-xs text-muted-foreground">
              KI-gestützter Dokumentations-Assistent
            </p>
          </div>
        </div>

        {/* Spacer */}
        <div className="flex-1" />

        {/* User Dropdown */}
        {user && (
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                variant="ghost"
                className="flex items-center gap-2"
                aria-label="User menu"
              >
                <Avatar className="h-8 w-8">
                  <AvatarFallback className="bg-primary text-primary-foreground text-sm">
                    {getUserInitials()}
                  </AvatarFallback>
                </Avatar>
                <div className="hidden md:flex flex-col items-start">
                  <span className="text-sm font-medium">{user.username}</span>
                  <StatusBadge
                    authLevel={user.authorization_level}
                    className="text-xs"
                  />
                </div>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-56">
              <DropdownMenuLabel>
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium">{user.username}</p>
                  <p className="text-xs text-muted-foreground">{user.email}</p>
                  <StatusBadge authLevel={user.authorization_level} />
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem onClick={() => navigate('/chat')}>
                <MessageSquare className="mr-2 h-4 w-4" />
                <span>Chat</span>
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => navigate('/profile')}>
                <User className="mr-2 h-4 w-4" />
                <span>Profil</span>
              </DropdownMenuItem>
              {user.authorization_level === 'admin' && (
                <DropdownMenuItem onClick={() => navigate('/admin')}>
                  <Shield className="mr-2 h-4 w-4" />
                  <span>Admin-Panel</span>
                </DropdownMenuItem>
              )}
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={handleLogout}
                className="text-destructive focus:text-destructive"
              >
                <LogOut className="mr-2 h-4 w-4" />
                <span>Abmelden</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        )}
      </div>
    </header>
  );
}
