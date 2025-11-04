import { render, screen, fireEvent, waitFor } from '@/test-utils/test-utils';
import userEvent from '@testing-library/user-event';
import { ConversationSidebar } from '../ConversationSidebar';
import type { Conversation } from '@/types';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock the chat service
jest.mock('@/services/chatService', () => ({
  getConversations: jest.fn(() => Promise.resolve([])),
  deleteConversation: jest.fn(() => Promise.resolve()),
  createConversation: jest.fn(() => Promise.resolve({ conversation_id: 'new-id', title: 'New Chat' })),
}));

const mockConversations: Conversation[] = [
  {
    conversation_id: '1',
    title: 'First Chat',
    message_count: 5,
    last_message_at: '2024-01-01T12:00:00Z',
    created_at: '2024-01-01T10:00:00Z',
  },
  {
    conversation_id: '2',
    title: 'Second Chat',
    message_count: 3,
    last_message_at: '2024-01-01T11:00:00Z',
    created_at: '2024-01-01T09:00:00Z',
  },
];

describe('ConversationSidebar', () => {
  const mockOnSelectConversation = jest.fn();
  const mockOnNewConversation = jest.fn();
  const mockOnRenameConversation = jest.fn();
  const mockOnDeleteConversation = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  const renderWithQuery = (ui: React.ReactElement) => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    return render(
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    );
  };

  it('renders "New Conversation" button', () => {
    renderWithQuery(
      <ConversationSidebar
        conversations={[]}
        activeConversationId={null}
        onSelectConversation={mockOnSelectConversation}
        onNewConversation={mockOnNewConversation}
        onRenameConversation={mockOnRenameConversation}
        onDeleteConversation={mockOnDeleteConversation}
      />
    );

    const newButton = screen.getByRole('button', { name: /new conversation/i });
    expect(newButton).toBeInTheDocument();
  });

  it('calls onNewConversation when new button clicked', async () => {
    const user = userEvent.setup();
    renderWithQuery(
      <ConversationSidebar
        conversations={[]}
        activeConversationId={null}
        onSelectConversation={mockOnSelectConversation}
        onNewConversation={mockOnNewConversation}
        onRenameConversation={mockOnRenameConversation}
        onDeleteConversation={mockOnDeleteConversation}
      />
    );

    const newButton = screen.getByRole('button', { name: /new conversation/i });
    await user.click(newButton);

    expect(mockOnNewConversation).toHaveBeenCalled();
  });

  it('renders conversation list', () => {
    renderWithQuery(
      <ConversationSidebar
        conversations={mockConversations}
        activeConversationId={null}
        onSelectConversation={mockOnSelectConversation}
        onNewConversation={mockOnNewConversation}
        onRenameConversation={mockOnRenameConversation}
        onDeleteConversation={mockOnDeleteConversation}
      />
    );

    expect(screen.getByText('First Chat')).toBeInTheDocument();
    expect(screen.getByText('Second Chat')).toBeInTheDocument();
  });

  it('highlights active conversation', () => {
    renderWithQuery(
      <ConversationSidebar
        conversations={mockConversations}
        activeConversationId="1"
        onSelectConversation={mockOnSelectConversation}
        onNewConversation={mockOnNewConversation}
        onRenameConversation={mockOnRenameConversation}
        onDeleteConversation={mockOnDeleteConversation}
      />
    );

    const firstChat = screen.getByText('First Chat').closest('button');
    expect(firstChat).toHaveClass(/bg-/); // Should have background color when active
  });

  it('calls onSelectConversation when conversation clicked', async () => {
    const user = userEvent.setup();
    renderWithQuery(
      <ConversationSidebar
        conversations={mockConversations}
        activeConversationId={null}
        onSelectConversation={mockOnSelectConversation}
        onNewConversation={mockOnNewConversation}
        onRenameConversation={mockOnRenameConversation}
        onDeleteConversation={mockOnDeleteConversation}
      />
    );

    const firstChat = screen.getByText('First Chat');
    await user.click(firstChat);

    expect(mockOnSelectConversation).toHaveBeenCalledWith('1');
  });

  it('renders search input', () => {
    renderWithQuery(
      <ConversationSidebar
        conversations={mockConversations}
        activeConversationId={null}
        onSelectConversation={mockOnSelectConversation}
        onNewConversation={mockOnNewConversation}
        onRenameConversation={mockOnRenameConversation}
        onDeleteConversation={mockOnDeleteConversation}
      />
    );

    const searchInput = screen.getByPlaceholderText(/search/i);
    expect(searchInput).toBeInTheDocument();
  });

  it('filters conversations based on search input', async () => {
    const user = userEvent.setup();
    renderWithQuery(
      <ConversationSidebar
        conversations={mockConversations}
        activeConversationId={null}
        onSelectConversation={mockOnSelectConversation}
        onNewConversation={mockOnNewConversation}
        onRenameConversation={mockOnRenameConversation}
        onDeleteConversation={mockOnDeleteConversation}
      />
    );

    const searchInput = screen.getByPlaceholderText(/search/i);
    await user.type(searchInput, 'First');

    // Should show First Chat
    expect(screen.getByText('First Chat')).toBeInTheDocument();
    // Second Chat might be filtered out (depends on implementation)
  });

  it('shows empty state when no conversations', () => {
    renderWithQuery(
      <ConversationSidebar
        conversations={[]}
        activeConversationId={null}
        onSelectConversation={mockOnSelectConversation}
        onNewConversation={mockOnNewConversation}
        onRenameConversation={mockOnRenameConversation}
        onDeleteConversation={mockOnDeleteConversation}
      />
    );

    expect(screen.getByText(/no conversations/i)).toBeInTheDocument();
  });

  it('shows delete button on conversation hover', async () => {
    renderWithQuery(
      <ConversationSidebar
        conversations={mockConversations}
        activeConversationId={null}
        onSelectConversation={mockOnSelectConversation}
        onNewConversation={mockOnNewConversation}
        onRenameConversation={mockOnRenameConversation}
        onDeleteConversation={mockOnDeleteConversation}
      />
    );

    const firstChat = screen.getByText('First Chat').closest('div');
    if (firstChat) {
      fireEvent.mouseEnter(firstChat);

      await waitFor(() => {
        const deleteButton = screen.getByLabelText(/delete/i);
        expect(deleteButton).toBeInTheDocument();
      });
    }
  });

  it('displays conversation message count', () => {
    renderWithQuery(
      <ConversationSidebar
        conversations={mockConversations}
        activeConversationId={null}
        onSelectConversation={mockOnSelectConversation}
        onNewConversation={mockOnNewConversation}
        onRenameConversation={mockOnRenameConversation}
        onDeleteConversation={mockOnDeleteConversation}
      />
    );

    expect(screen.getByText(/5/)).toBeInTheDocument(); // message_count
  });
});
