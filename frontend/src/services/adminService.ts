import apiClient from './api';
import type { PendingUser, User, PaginatedResponse } from '@/types';

export const adminService = {
  async getPendingUsers(): Promise<PendingUser[]> {
    const response = await apiClient.get('/api/admin/users/pending');
    return response.data.pending_users || [];
  },

  async approveUser(
    userId: string,
    authorizationLevel: 'regular' | 'superuser' | 'admin'
  ): Promise<{ message: string }> {
    const response = await apiClient.post(`/api/admin/users/${userId}/approve`, {
      authorization_level: authorizationLevel,
    });
    return response.data;
  },

  async rejectUser(userId: string, reason?: string): Promise<{ message: string }> {
    const response = await apiClient.post(`/api/admin/users/${userId}/reject`, {
      reason,
    });
    return response.data;
  },

  async getUsers(params?: {
    status?: string;
    authorization_level?: string;
    search?: string;
    page?: number;
  }): Promise<PaginatedResponse<User>> {
    const response = await apiClient.get('/api/admin/users', { params });
    // Transform backend response to match PaginatedResponse structure
    const data = response.data;
    return {
      items: data.users || [],
      total: data.total || 0,
      page: params?.page || 1,
      per_page: data.limit || 20,
      total_pages: Math.ceil((data.total || 0) / (data.limit || 20))
    };
  },

  async updateUserAuthorization(
    userId: string,
    authorizationLevel: 'regular' | 'superuser' | 'admin'
  ): Promise<{ message: string }> {
    const response = await apiClient.put(`/api/admin/users/${userId}/authorization`, {
      authorization_level: authorizationLevel,
    });
    return response.data;
  },

  async updateUserStatus(
    userId: string,
    status: 'active' | 'suspended'
  ): Promise<{ message: string }> {
    const response = await apiClient.put(`/api/admin/users/${userId}/status`, {
      status,
    });
    return response.data;
  },
};
