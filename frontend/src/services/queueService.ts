import apiClient from './api';

export interface QueueItem {
  queue_id: string;
  document_id: string;
  filename: string;
  category: string;
  file_size_bytes: number;
  uploader_name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  position: number;
  added_at: string;
  started_at?: string;
  completed_at?: string;
  processing_progress?: number;
  processing_step?: string;
  error_message?: string;
}

export interface QueueStats {
  total: number;
  pending: number;
  processing: number;
  completed: number;
  failed: number;
}

export const queueService = {
  async getQueue(): Promise<QueueItem[]> {
    const response = await apiClient.get('/api/queue');
    return response.data;
  },

  async getQueueStats(): Promise<QueueStats> {
    const response = await apiClient.get('/api/queue/stats');
    return response.data;
  },

  async removeFromQueue(queueId: string): Promise<void> {
    await apiClient.delete(`/api/queue/${queueId}`);
  },

  async clearQueue(): Promise<{ deleted_count: number }> {
    const response = await apiClient.post('/api/queue/clear');
    return response.data;
  },
};
