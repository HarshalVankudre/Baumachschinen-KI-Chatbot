import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';
import type { User } from '@/types';

interface ProtectedRouteProps {
  children: React.ReactNode;
  requiredLevel?: User['authorization_level'][];
}

export function ProtectedRoute({
  children,
  requiredLevel,
}: ProtectedRouteProps) {
  const { isAuthenticated, user } = useAuthStore();

  console.log('[ProtectedRoute] Checking auth:', { isAuthenticated, user, requiredLevel });

  if (!isAuthenticated) {
    console.log('[ProtectedRoute] Not authenticated, redirecting to /login');
    return <Navigate to="/login" replace />;
  }

  if (requiredLevel && user && !requiredLevel.includes(user.authorization_level)) {
    console.log('[ProtectedRoute] Insufficient authorization level, redirecting to /forbidden');
    return <Navigate to="/forbidden" replace />;
  }

  console.log('[ProtectedRoute] Auth check passed, rendering protected content');
  return <>{children}</>;
}
