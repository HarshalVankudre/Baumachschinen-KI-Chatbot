import axios, { AxiosError } from 'axios';
import type { AxiosInstance } from 'axios';
import { useAuthStore } from '@/store/authStore';

// HARDCODED FOR DEBUGGING - FORCE USE CORRECT IP
const API_BASE_URL = 'http://136.116.238.200:8000';

// Debug logging
console.log('[API] HARDCODED API_BASE_URL:', API_BASE_URL);
console.log('[API] VITE_API_URL from env (ignored):', import.meta.env.VITE_API_URL);
console.log('[API] All env vars:', import.meta.env);

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  withCredentials: true, // Important for cookie-based auth
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    if (import.meta.env.DEV) {
      console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    return response;
  },
  (error: AxiosError) => {
    const status = error.response?.status;
    const url = error.config?.url;
    const errorData = error.response?.data as any;

    // Don't redirect on auth-related endpoint failures
    const isAuthEndpoint = url?.includes('/auth/');

    if (status === 401 && !isAuthEndpoint) {
      // Unauthorized - clear auth state
      const authStore = useAuthStore.getState();

      // Only logout if we're actually authenticated
      // This prevents issues during login
      if (authStore.isAuthenticated) {
        console.log('[API Interceptor] 401 Unauthorized - clearing auth state');
        authStore.logout();

        // Only redirect if not already on login page
        if (window.location.pathname !== '/login') {
          // Use window.location for redirect to ensure clean state
          window.location.replace('/login');
        }
      }
    } else if (status === 403) {
      // Forbidden - show error
      console.error('Access forbidden:', errorData);
    } else if (status === 429) {
      // Rate limit exceeded - show friendly message
      console.warn('Rate limit exceeded:', errorData);

      // Extract retry-after header if available
      const retryAfter = error.response?.headers['retry-after'];
      const waitTime = retryAfter ? `${retryAfter} seconds` : 'a moment';

      // You can dispatch a toast notification here if you have a global toast system
      // For now, we'll just log it and let the calling component handle it
      if (typeof window !== 'undefined') {
        // Dispatch custom event that components can listen to
        window.dispatchEvent(new CustomEvent('rate-limit-exceeded', {
          detail: {
            message: `Rate limit exceeded. Please wait ${waitTime} before trying again.`,
            retryAfter: retryAfter ? parseInt(retryAfter) : null
          }
        }));
      }
    } else if (status === 500) {
      // Server error - show toast
      console.error('Server error:', errorData);
    }

    return Promise.reject(error);
  }
);

export default apiClient;

// Helper function for retry logic
export async function retryRequest<T>(
  fn: () => Promise<T>,
  retries = 3,
  delay = 1000
): Promise<T> {
  try {
    return await fn();
  } catch (error) {
    if (retries === 0) throw error;
    await new Promise((resolve) => setTimeout(resolve, delay));
    return retryRequest(fn, retries - 1, delay * 2);
  }
}
