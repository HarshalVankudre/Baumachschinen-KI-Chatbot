import axios from 'axios';
import type { AxiosInstance } from 'axios';

// Mock axios instance for testing
// This file mocks the api.ts service to avoid import.meta issues in Jest
const apiClient: AxiosInstance = axios.create({
  baseURL: 'http://localhost:8000',
  timeout: 30000,
  withCredentials: true,
  headers: {
    'Content-Type': 'application/json',
  },
});

export default apiClient;

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
