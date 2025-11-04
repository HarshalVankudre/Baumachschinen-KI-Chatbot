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
      const response = await authService.login(username, password);
      setUser(response);
      return response;
    } catch (err: any) {
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
