import { useAuthStore } from '@/store/authStore';
import { authService } from '@/services/authService';
import { useState } from 'react';
import type { User } from '@/types';

// Constants
const STORE_PERSIST_DELAY_MS = 100;

/**
 * Authentication hook providing login, register, and logout functionality.
 *
 * Integrates with Zustand auth store and backend auth service.
 * Handles loading states, errors, and user session persistence.
 *
 * @returns Authentication state and methods
 */
export function useAuth() {
  const { user, isAuthenticated, setUser, logout: logoutStore } = useAuthStore();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Log in a user with username and password.
   *
   * @param username - User's username
   * @param password - User's password
   * @returns User object on success
   * @throws Error if login fails or response is invalid
   */
  const login = async (username: string, password: string): Promise<User> => {
    setLoading(true);
    setError(null);
    try {
      console.log('[useAuth] Calling authService.login');
      const response = await authService.login(username, password);
      console.log('[useAuth] Login response:', response);

      // Backend returns user data directly (not nested)
      if (!response || !response.user_id) {
        console.error('[useAuth] Invalid response structure:', response);
        throw new Error('Invalid login response');
      }

      // Ensure user is set in store before returning
      console.log('[useAuth] Setting user in store:', response);
      setUser(response);

      // Small delay to ensure Zustand persist middleware has time to save
      await new Promise(resolve => setTimeout(resolve, STORE_PERSIST_DELAY_MS));

      // Return the user object for the component to use
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

  /**
   * Register a new user account.
   *
   * @param email - User's email address
   * @param username - Desired username
   * @param password - User's password
   * @param confirmPassword - Password confirmation
   * @returns Registration response
   * @throws Error if registration fails
   */
  const register = async (
    email: string,
    username: string,
    password: string,
    confirmPassword: string
  ): Promise<any> => {
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

  /**
   * Log out the current user.
   *
   * Calls backend logout endpoint and clears local session.
   * Errors are logged but don't prevent logout.
   */
  const logout = async (): Promise<void> => {
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
