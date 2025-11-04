import { create } from 'zustand';
import type { Conversation } from '@/types';

interface ChatState {
  activeConversationId: string | null;
  conversations: Conversation[];
  isStreaming: boolean;
  streamingMessage: string;
  setActiveConversation: (id: string | null) => void;
  setConversations: (conversations: Conversation[]) => void;
  addConversation: (conversation: Conversation) => void;
  updateConversation: (id: string, updates: Partial<Conversation>) => void;
  deleteConversation: (id: string) => void;
  setStreaming: (streaming: boolean) => void;
  setStreamingMessage: (message: string) => void;
  appendStreamingToken: (token: string) => void;
}

export const useChatStore = create<ChatState>((set) => ({
  activeConversationId: null,
  conversations: [],
  isStreaming: false,
  streamingMessage: '',
  setActiveConversation: (id) => set({ activeConversationId: id }),
  setConversations: (conversations) => set({ conversations }),
  addConversation: (conversation) =>
    set((state) => ({
      conversations: [conversation, ...state.conversations],
    })),
  updateConversation: (id, updates) =>
    set((state) => ({
      conversations: state.conversations.map((conv) =>
        conv.conversation_id === id ? { ...conv, ...updates } : conv
      ),
    })),
  deleteConversation: (id) =>
    set((state) => ({
      conversations: state.conversations.filter(
        (conv) => conv.conversation_id !== id
      ),
      activeConversationId:
        state.activeConversationId === id ? null : state.activeConversationId,
    })),
  setStreaming: (streaming) => set({ isStreaming: streaming }),
  setStreamingMessage: (message) => set({ streamingMessage: message }),
  appendStreamingToken: (token) =>
    set((state) => ({
      streamingMessage: state.streamingMessage + token,
    })),
}));
