import apiClient from './api';
import type { LoginResponse, User } from '@/types';

export const authService = {
  async login(username: string, password: string): Promise<LoginResponse> {
    console.log('[authService] Sending login request for:', username);
    const response = await apiClient.post('/api/auth/login', {
      username,
      password,
    });
    console.log('[authService] API response:', response);
    console.log('[authService] API response.data:', response.data);
    return response.data;
  },

  async register(
    email: string,
    username: string,
    password: string,
    confirmPassword: string
  ): Promise<{ message: string }> {
    const response = await apiClient.post('/api/auth/register', {
      email,
      username,
      password,
      confirm_password: confirmPassword,
    });
    return response.data;
  },

  async verifyEmail(token: string): Promise<{ message: string }> {
    const response = await apiClient.post('/api/auth/verify-email', {
      token,
    });
    return response.data;
  },

  async logout(): Promise<void> {
    await apiClient.post('/api/auth/logout');
  },

  async getCurrentUser(): Promise<User> {
    const response = await apiClient.get('/api/auth/me');
    return response.data;
  },

  async changePassword(
    currentPassword: string,
    newPassword: string
  ): Promise<{ message: string }> {
    const response = await apiClient.put('/api/user/password', {
      current_password: currentPassword,
      new_password: newPassword,
    });
    return response.data;
  },

  async requestPasswordReset(email: string): Promise<{ message: string }> {
    const response = await apiClient.post('/api/auth/forgot-password', {
      email,
    });
    return response.data;
  },

  async verifyResetToken(token: string): Promise<{ message: string }> {
    const response = await apiClient.get(`/api/auth/reset-password/verify/${token}`);
    return response.data;
  },

  async resetPassword(
    token: string,
    newPassword: string,
    confirmPassword: string
  ): Promise<{ message: string }> {
    const response = await apiClient.post('/api/auth/reset-password', {
      token,
      new_password: newPassword,
      confirm_password: confirmPassword,
    });
    return response.data;
  },
};
