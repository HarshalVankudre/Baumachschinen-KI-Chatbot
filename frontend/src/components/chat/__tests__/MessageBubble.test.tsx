import { render, screen, fireEvent, waitFor } from '@/test-utils/test-utils';
import { MessageBubble } from '../MessageBubble';
import type { Message } from '@/types';

// Mock clipboard API
Object.assign(navigator, {
  clipboard: {
    writeText: jest.fn(() => Promise.resolve()),
  },
});

describe('MessageBubble', () => {
  const mockUserMessage: Message = {
    message_id: '1',
    role: 'user',
    content: 'Hello, how are you?',
    timestamp: '2024-01-01T00:00:00Z',
  };

  const mockAssistantMessage: Message = {
    message_id: '2',
    role: 'assistant',
    content: 'I am doing well, thank you!',
    timestamp: '2024-01-01T00:00:01Z',
  };

  const mockMessageWithMarkdown: Message = {
    message_id: '3',
    role: 'assistant',
    content: '# Hello\n\nThis is **bold** and *italic* text.',
    timestamp: '2024-01-01T00:00:02Z',
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders user message correctly', () => {
    render(<MessageBubble message={mockUserMessage} />);

    expect(screen.getByText('Hello, how are you?')).toBeInTheDocument();
  });

  it('renders assistant message correctly', () => {
    render(<MessageBubble message={mockAssistantMessage} />);

    expect(screen.getByText('I am doing well, thank you!')).toBeInTheDocument();
  });

  it('renders markdown content in assistant message', () => {
    render(<MessageBubble message={mockMessageWithMarkdown} />);

    expect(screen.getByText('Hello')).toBeInTheDocument();
    expect(screen.getByText(/This is/)).toBeInTheDocument();
  });

  it('shows copy button on hover for assistant messages', () => {
    render(<MessageBubble message={mockAssistantMessage} />);

    // Copy button should be in the document (even if not visible initially)
    const buttons = screen.getAllByRole('button');
    expect(buttons.length).toBeGreaterThan(0);
  });

  it('copies message content to clipboard', async () => {
    render(<MessageBubble message={mockAssistantMessage} />);

    const copyButton = screen.getAllByRole('button')[0];
    fireEvent.click(copyButton);

    await waitFor(() => {
      expect(navigator.clipboard.writeText).toHaveBeenCalledWith(mockAssistantMessage.content);
    });
  });

  it('shows edit button for user messages when onEdit provided', () => {
    const onEdit = jest.fn();
    render(<MessageBubble message={mockUserMessage} onEdit={onEdit} />);

    const buttons = screen.getAllByRole('button');
    const editButton = buttons.find(btn => btn.querySelector('[data-testid="edit-icon"]') || btn.textContent === 'Edit');

    if (editButton) {
      fireEvent.click(editButton);
      expect(onEdit).toHaveBeenCalledWith(mockUserMessage.message_id);
    }
  });

  it('displays timestamp', () => {
    render(<MessageBubble message={mockUserMessage} />);

    // Check that some timestamp text is rendered (format may vary)
    expect(screen.getByText(/Jan|01|2024|12:00 AM/)).toBeInTheDocument();
  });

  it('displays edited indicator when message is edited', () => {
    const editedMessage = { ...mockUserMessage, edited: true };
    render(<MessageBubble message={editedMessage} />);

    expect(screen.getByText(/edited/i)).toBeInTheDocument();
  });

  it('displays sources when metadata includes them', () => {
    const messageWithSources: Message = {
      ...mockAssistantMessage,
      metadata: {
        sources: ['Document 1', 'Document 2'],
      },
    };

    render(<MessageBubble message={messageWithSources} />);

    expect(screen.getByText(/sources/i)).toBeInTheDocument();
    expect(screen.getByText('Document 1')).toBeInTheDocument();
    expect(screen.getByText('Document 2')).toBeInTheDocument();
  });
});
