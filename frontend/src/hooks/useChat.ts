import { useState, useCallback, useRef } from 'react';
import { useChatStore } from '@/store/chatStore';
import { chatService } from '@/services/chatService';
import type { Message } from '@/types';

interface UseChatOptions {
  conversationId?: string;
  onError?: (error: Error) => void;
  onMessageComplete?: (message: Message) => void;
}

interface StreamEvent {
  type: 'token' | 'source' | 'complete' | 'error';
  content?: string;
  sources?: string[];
  message?: Message;
  error?: string;
}

export function useChat(options: UseChatOptions = {}) {
  const storeConversationId = useChatStore((state) => state.activeConversationId);
  const conversationId = options.conversationId || storeConversationId;

  const [messages, setMessages] = useState<Message[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const [currentStreamingMessage, setCurrentStreamingMessage] = useState<string>('');
  const [error, setError] = useState<Error | null>(null);

  const abortControllerRef = useRef<AbortController | null>(null);

  const loadMessages = useCallback(async (convId: string) => {
    try {
      const conversation = await chatService.getConversation(convId);
      setMessages(conversation.messages || []);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to load messages');
      setError(error);
      options.onError?.(error);
    }
  }, [options]);

  const sendMessage = useCallback(async (content: string) => {
    if (!conversationId) {
      const error = new Error('No active conversation');
      setError(error);
      options.onError?.(error);
      return;
    }

    // Add user message immediately
    const userMessage: Message = {
      message_id: `temp-${Date.now()}`,
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMessage]);

    // Start streaming AI response
    setIsStreaming(true);
    setCurrentStreamingMessage('');
    setError(null);

    try {
      abortControllerRef.current = new AbortController();

      const response = await fetch(
        `${import.meta.env.VITE_API_URL || 'http://localhost:8000'}/api/chat/conversations/${conversationId}/messages`,
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ message: content }),
          credentials: 'include',
          signal: abortControllerRef.current.signal,
        }
      );

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const reader = response.body?.getReader();
      if (!reader) {
        throw new Error('No response body');
      }

      const decoder = new TextDecoder();
      let buffer = '';
      let streamedContent = '';
      let sources: string[] = [];

      while (true) {
        const { done, value } = await reader.read();

        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop() || '';

        for (const line of lines) {
          if (!line.trim() || !line.startsWith('data: ')) continue;

          try {
            const data: StreamEvent = JSON.parse(line.slice(6));

            if (data.type === 'token' && data.content) {
              streamedContent += data.content;
              setCurrentStreamingMessage(streamedContent);
            } else if (data.type === 'source' && data.sources) {
              sources = data.sources;
            } else if (data.type === 'complete' && data.message) {
              const completeMessage: Message = {
                ...data.message,
                metadata: {
                  ...data.message.metadata,
                  sources,
                },
              };

              // Replace streaming message with complete message
              setMessages(prev => [...prev, completeMessage]);
              options.onMessageComplete?.(completeMessage);
            } else if (data.type === 'error') {
              throw new Error(data.error || 'Streaming error');
            }
          } catch (parseError) {
            console.error('Error parsing SSE data:', parseError);
          }
        }
      }
    } catch (err) {
      if (err instanceof Error && err.name === 'AbortError') {
        // Streaming was cancelled
        return;
      }

      const error = err instanceof Error ? err : new Error('Failed to send message');
      setError(error);
      options.onError?.(error);

      // Remove user message on error
      setMessages(prev => prev.filter(m => m.message_id !== userMessage.message_id));
    } finally {
      setIsStreaming(false);
      setCurrentStreamingMessage('');
      abortControllerRef.current = null;
    }
  }, [conversationId, options]);

  const cancelStreaming = useCallback(() => {
    abortControllerRef.current?.abort();
    setIsStreaming(false);
    setCurrentStreamingMessage('');
  }, []);

  const editMessage = useCallback(async (messageId: string, newContent: string) => {
    if (!conversationId) return;

    try {
      // Update message locally
      setMessages(prev =>
        prev.map(m =>
          m.message_id === messageId
            ? { ...m, content: newContent, edited: true }
            : m
        )
      );

      // Send edit request and stream new response
      await sendMessage(newContent);
    } catch (err) {
      const error = err instanceof Error ? err : new Error('Failed to edit message');
      setError(error);
      options.onError?.(error);
    }
  }, [conversationId, sendMessage, options]);

  const clearMessages = useCallback(() => {
    setMessages([]);
    setCurrentStreamingMessage('');
    setError(null);
  }, []);

  return {
    messages,
    isStreaming,
    currentStreamingMessage,
    error,
    sendMessage,
    cancelStreaming,
    editMessage,
    loadMessages,
    clearMessages,
  };
}
