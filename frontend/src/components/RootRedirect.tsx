import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

/**
 * RootRedirect Component
 *
 * Redirects users from the root path based on authentication status:
 * - Authenticated users -> /chat
 * - Unauthenticated users -> /login
 */
export function RootRedirect() {
  const { isAuthenticated } = useAuthStore();

  if (isAuthenticated) {
    return <Navigate to="/chat" replace />;
  }

  return <Navigate to="/login" replace />;
}
