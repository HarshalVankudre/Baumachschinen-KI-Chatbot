import { renderHook, waitFor } from '@/test-utils/test-utils';
import { useChat } from '../useChat';
import * as chatService from '@/services/chatService';

jest.mock('@/services/chatService');

describe('useChat', () => {
  const mockConversation = {
    conversation_id: '1',
    title: 'Test Chat',
    message_count: 2,
    last_message_at: '2024-01-01T12:00:00Z',
    created_at: '2024-01-01T10:00:00Z',
    messages: [
      {
        message_id: 'm1',
        role: 'user' as const,
        content: 'Hello',
        timestamp: '2024-01-01T10:00:00Z',
      },
      {
        message_id: 'm2',
        role: 'assistant' as const,
        content: 'Hi there!',
        timestamp: '2024-01-01T10:00:01Z',
      },
    ],
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('initializes with empty state', () => {
    const { result } = renderHook(() => useChat());

    expect(result.current.messages).toEqual([]);
    expect(result.current.isLoading).toBe(false);
    expect(result.current.isStreaming).toBe(false);
  });

  it('loads conversation messages', async () => {
    (chatService.getConversation as jest.Mock).mockResolvedValue(mockConversation);

    const { result } = renderHook(() => useChat());

    await result.current.loadConversation('1');

    await waitFor(() => {
      expect(result.current.messages).toHaveLength(2);
      expect(result.current.messages[0].content).toBe('Hello');
    });
  });

  it('handles send message', async () => {
    (chatService.sendMessage as jest.Mock).mockResolvedValue({
      message_id: 'm3',
      role: 'assistant',
      content: 'Response',
    });

    const { result } = renderHook(() => useChat());

    await result.current.sendMessage('1', 'Test message');

    await waitFor(() => {
      expect(chatService.sendMessage).toHaveBeenCalledWith('1', 'Test message');
    });
  });

  it('sets streaming state during message send', async () => {
    (chatService.sendMessage as jest.Mock).mockImplementation(
      () => new Promise(resolve => setTimeout(resolve, 100))
    );

    const { result } = renderHook(() => useChat());

    const sendPromise = result.current.sendMessage('1', 'Test');

    expect(result.current.isStreaming).toBe(true);

    await sendPromise;

    await waitFor(() => {
      expect(result.current.isStreaming).toBe(false);
    });
  });

  it('handles errors when loading conversation', async () => {
    (chatService.getConversation as jest.Mock).mockRejectedValue(
      new Error('Failed to load')
    );

    const { result } = renderHook(() => useChat());

    await result.current.loadConversation('1');

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });
  });

  it('handles errors when sending message', async () => {
    (chatService.sendMessage as jest.Mock).mockRejectedValue(
      new Error('Failed to send')
    );

    const { result } = renderHook(() => useChat());

    await result.current.sendMessage('1', 'Test');

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });
  });

  it('clears messages on clear', () => {
    const { result } = renderHook(() => useChat());

    result.current.clearMessages();

    expect(result.current.messages).toEqual([]);
  });

  it('updates existing message', () => {
    const { result } = renderHook(() => useChat());

    // Add initial message
    result.current.addMessage({
      message_id: 'm1',
      role: 'user',
      content: 'Original',
      timestamp: '2024-01-01T00:00:00Z',
    });

    // Update message
    result.current.updateMessage('m1', { content: 'Updated' });

    const updatedMessage = result.current.messages.find(m => m.message_id === 'm1');
    expect(updatedMessage?.content).toBe('Updated');
  });

  it('adds new message to list', () => {
    const { result } = renderHook(() => useChat());

    result.current.addMessage({
      message_id: 'm1',
      role: 'user',
      content: 'New message',
      timestamp: '2024-01-01T00:00:00Z',
    });

    expect(result.current.messages).toHaveLength(1);
    expect(result.current.messages[0].content).toBe('New message');
  });
});
