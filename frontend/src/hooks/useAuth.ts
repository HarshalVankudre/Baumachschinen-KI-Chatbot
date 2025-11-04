import { useAuthStore } from '@/store/authStore';
import { authService } from '@/services/authService';
import { useState } from 'react';

export function useAuth() {
  const { user, isAuthenticated, setUser, logout: logoutStore } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = async (username: string, password: string) => {
    setLoading(true);
    setError(null);
    try {
      console.log('[useAuth] Calling authService.login');
      const response = await authService.login(username, password);
      console.log('[useAuth] Login response:', response);

      // Backend returns user data directly (not nested in response.user)
      if (!response || !response.user_id) {
        console.error('[useAuth] Invalid response structure:', response);
        throw new Error('Invalid login response');
      }

      // Ensure user is set in store before returning
      console.log('[useAuth] Setting user in store:', response);
      setUser(response);

      // Small delay to ensure Zustand persist middleware has time to save
      await new Promise(resolve => setTimeout(resolve, 100));

      // Return the full response for the component to use
      console.log('[useAuth] Returning successful response');
      return response;
    } catch (err: any) {
      console.error('[useAuth] Login failed:', err);
      const errorMsg = err.response?.data?.message || 'Login failed';
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const register = async (email: string, username: string, password: string, confirmPassword: string) => {
    setLoading(true);
    setError(null);
    try {
      const response = await authService.register(email, username, password, confirmPassword);
      return response;
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || 'Registration failed';
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  };

  const logout = async () => {
    setLoading(true);
    try {
      await authService.logout();
    } catch (err) {
      console.error('Logout error:', err);
    } finally {
      logoutStore();
      setLoading(false);
    }
  };

  return {
    user,
    isAuthenticated,
    loading,
    error,
    login,
    register,
    logout,
  };
}
