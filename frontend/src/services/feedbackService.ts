import apiClient from './api';
import type {
  MessageFeedbackRequest,
  MessageFeedbackResponse,
  ConversationFeedbackRequest,
  ConversationFeedbackResponse,
  FeedbackStats,
} from '@/types/feedback';

export const feedbackService = {
  /**
   * Submit feedback for a specific message
   * One-click feedback for thumbs up/down
   */
  async submitMessageFeedback(
    data: MessageFeedbackRequest
  ): Promise<MessageFeedbackResponse> {
    const response = await apiClient.post('/api/chat/feedback/message', null, {
      params: {
        conversation_id: data.conversation_id,
        message_id: data.message_id,
        feedback_type: data.feedback_type,
        comment: data.comment,
      },
    });
    return response.data;
  },

  /**
   * Submit feedback for entire conversation
   * Used when user completes a conversation
   */
  async submitConversationFeedback(
    data: ConversationFeedbackRequest
  ): Promise<ConversationFeedbackResponse> {
    const response = await apiClient.post(
      '/api/chat/feedback/conversation',
      null,
      {
        params: {
          conversation_id: data.conversation_id,
          overall_rating: data.overall_rating,
          what_went_well: data.what_went_well,
          what_needs_improvement: data.what_needs_improvement,
          suggestions: data.suggestions,
        },
      }
    );
    return response.data;
  },

  /**
   * Get feedback statistics
   * Regular users see their own stats, admins see all
   */
  async getFeedbackStats(days: number = 30): Promise<FeedbackStats> {
    const response = await apiClient.get('/api/chat/feedback/stats', {
      params: { days },
    });
    return response.data;
  },
};
