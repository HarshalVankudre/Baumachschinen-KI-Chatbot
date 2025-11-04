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

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (requiredLevel && user && !requiredLevel.includes(user.authorization_level)) {
    return <Navigate to="/forbidden" replace />;
  }

  return <>{children}</>;
}
