import axios, { AxiosError } from 'axios';
import type { AxiosInstance } from 'axios';
import { useAuthStore } from '@/store/authStore';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

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
      console.error('Access forbidden:', error.response?.data);
    } else if (status === 500) {
      // Server error - show toast
      console.error('Server error:', error.response?.data);
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
