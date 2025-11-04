import apiClient from './api';
import type { Document, PaginatedResponse } from '@/types';

export const documentService = {
  async getDocuments(params?: {
    category?: string;
    search?: string;
    uploaded_by?: string;
    start_date?: string;
    end_date?: string;
    page?: number;
  }): Promise<PaginatedResponse<Document>> {
    try {
      // Use extended timeout for document listing (60 seconds)
      // This allows the backend query timeout logic to handle slow queries gracefully
      const response = await apiClient.get('/api/documents', {
        params,
        timeout: 60000, // 60 seconds
      });
      // Transform backend response to match PaginatedResponse structure
      const data = response.data;
      return {
        items: data.documents || [],
        total: data.total || 0,
        page: params?.page || 1,
        per_page: data.limit || 50,
        total_pages: Math.ceil((data.total || 0) / (data.limit || 50))
      };
    } catch (error: any) {
      console.error('Error fetching documents:', error);

      // Handle authentication errors
      if (error.response?.status === 401) {
        console.error('Not authenticated. User session may have expired.');
        // The axios interceptor will handle redirect to login
        throw new Error('Authentication required. Please log in again.');
      }

      // Handle authorization errors
      if (error.response?.status === 403) {
        console.error('Access forbidden. Insufficient permissions.');
        throw new Error('You do not have permission to access documents. Admin access required.');
      }

      // Handle timeout errors
      if (error.code === 'ECONNABORTED' || error.message?.includes('timeout')) {
        console.error('Document fetch timed out. Server may be processing a large dataset.');
        throw new Error('Request timed out. The server is taking too long to respond. Please try again with filters to narrow your search.');
      }

      // Handle gateway timeout
      if (error.response?.status === 504) {
        console.error('Gateway timeout: Backend query took too long. Try using filters to narrow results.');
        throw new Error('Server query timed out. Try using search filters to narrow your results.');
      }

      // Handle network errors
      if (error.code === 'ERR_NETWORK' || error.code === 'ERR_CONNECTION_RESET') {
        console.error('Network error: Cannot connect to backend server.');
        throw new Error('Cannot connect to server. Please ensure the backend is running and try again.');
      }

      // Handle server errors
      if (error.response?.status === 500) {
        console.error('Server error:', error.response?.data);
        throw new Error('Server error occurred. Please try again or contact support if the problem persists.');
      }

      // Generic error
      const errorMessage = error.response?.data?.detail || error.message || 'An unexpected error occurred';
      throw new Error(`Failed to fetch documents: ${errorMessage}`);
    }
  },

  async uploadDocument(
    file: File,
    category: string,
    onProgress?: (progress: number) => void
  ): Promise<Document> {
    const formData = new FormData();
    formData.append('file', file);
    formData.append('category', category);

    const response = await apiClient.post('/api/documents/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
      timeout: 120000, // 2 minutes for file upload
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total && onProgress) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress(progress);
        }
      },
    });
    return response.data;
  },

  async deleteDocument(id: string): Promise<void> {
    await apiClient.delete(`/api/documents/${id}`);
  },
};
