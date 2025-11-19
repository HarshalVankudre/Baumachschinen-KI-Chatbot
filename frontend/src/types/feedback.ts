// Feedback Types

export type FeedbackType = 'helpful' | 'not_helpful' | 'incorrect' | 'incomplete' | 'other';

export interface MessageFeedbackRequest {
  conversation_id: string;
  message_id: string;
  feedback_type: FeedbackType;
  comment?: string;
}

export interface MessageFeedbackResponse {
  feedback_id: string;
  message: string;
  conversation_id: string;
  message_id: string;
  feedback_type: FeedbackType;
}

export interface ConversationFeedbackRequest {
  conversation_id: string;
  overall_rating: number; // 1-5
  what_went_well?: string;
  what_needs_improvement?: string;
  suggestions?: string;
}

export interface ConversationFeedbackResponse {
  feedback_id: string;
  message: string;
  conversation_id: string;
  overall_rating: number;
}

export interface FeedbackStats {
  total_feedback: number;
  avg_rating: number;
  helpful_count: number;
  feedback_types: Record<FeedbackType, number>;
}
