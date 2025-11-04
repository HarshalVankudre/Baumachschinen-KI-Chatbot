import apiClient from './api';
import type { Conversation } from '@/types';

export const chatService = {
  async getConversations(): Promise<Conversation[]> {
    const response = await apiClient.get('/api/chat/conversations');
    return response.data.conversations || [];
  },

  async getConversation(id: string): Promise<Conversation> {
    const response = await apiClient.get(`/api/chat/conversations/${id}`);
    return response.data;
  },

  async createConversation(title: string): Promise<Conversation> {
    const response = await apiClient.post('/api/chat/conversations', {
      title,
    });
    return response.data;
  },

  async updateConversation(
    id: string,
    title: string
  ): Promise<Conversation> {
    const response = await apiClient.put(`/api/chat/conversations/${id}`, {
      title,
    });
    return response.data;
  },

  async deleteConversation(id: string): Promise<void> {
    await apiClient.delete(`/api/chat/conversations/${id}`);
  },

  async sendMessage(
    conversationId: string,
    content: string,
    editedMessageId?: string
  ): Promise<Response> {
    // This returns a fetch Response for streaming
    const url = `${apiClient.defaults.baseURL}/api/chat/conversations/${conversationId}/messages`;

    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      credentials: 'include',
      body: JSON.stringify({
        message: content,
        edited_message_id: editedMessageId,
      }),
    });
  },

  async exportConversation(
    id: string,
    format: 'markdown' | 'pdf' = 'markdown'
  ): Promise<Blob> {
    const response = await apiClient.get(
      `/api/chat/conversations/${id}/export`,
      {
        params: { format },
        responseType: 'blob',
      }
    );
    return response.data;
  },

  async searchConversations(query: string): Promise<Conversation[]> {
    const response = await apiClient.get('/api/chat/conversations', {
      params: { search: query },
    });
    return response.data.conversations || [];
  },
};
