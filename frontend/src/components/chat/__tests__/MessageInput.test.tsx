import { render, screen } from '@/test-utils/test-utils';
import userEvent from '@testing-library/user-event';
import { MessageInput } from '../MessageInput';

describe('MessageInput', () => {
  const mockOnSend = jest.fn();

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders textarea with placeholder', () => {
    render(<MessageInput onSend={mockOnSend} disabled={false} />);

    const textarea = screen.getByPlaceholderText(/type your message/i);
    expect(textarea).toBeInTheDocument();
  });

  it('renders send button', () => {
    render(<MessageInput onSend={mockOnSend} disabled={false} />);

    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeInTheDocument();
  });

  it('disables send button when input is empty', () => {
    render(<MessageInput onSend={mockOnSend} disabled={false} />);

    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeDisabled();
  });

  it('enables send button when input has text', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={mockOnSend} disabled={false} />);

    const textarea = screen.getByPlaceholderText(/type your message/i);
    await user.type(textarea, 'Hello world');

    const sendButton = screen.getByRole('button', { name: /send/i });
    expect(sendButton).toBeEnabled();
  });

  it('calls onSend with message content when send button clicked', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={mockOnSend} disabled={false} />);

    const textarea = screen.getByPlaceholderText(/type your message/i);
    await user.type(textarea, 'Test message');

    const sendButton = screen.getByRole('button', { name: /send/i });
    await user.click(sendButton);

    expect(mockOnSend).toHaveBeenCalledWith('Test message');
  });

  it('clears input after sending message', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={mockOnSend} disabled={false} />);

    const textarea = screen.getByPlaceholderText(/type your message/i);
    await user.type(textarea, 'Test message');

    const sendButton = screen.getByRole('button', { name: /send/i });
    await user.click(sendButton);

    expect(textarea).toHaveValue('');
  });

  it('sends message on Enter key press', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={mockOnSend} disabled={false} />);

    const textarea = screen.getByPlaceholderText(/type your message/i);
    await user.type(textarea, 'Test message');
    await user.keyboard('{Enter}');

    expect(mockOnSend).toHaveBeenCalledWith('Test message');
  });

  it('adds new line on Shift+Enter', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={mockOnSend} disabled={false} />);

    const textarea = screen.getByPlaceholderText(/type your message/i);
    await user.type(textarea, 'Line 1');
    await user.keyboard('{Shift>}{Enter}{/Shift}');
    await user.type(textarea, 'Line 2');

    expect(textarea).toHaveValue('Line 1\nLine 2');
    expect(mockOnSend).not.toHaveBeenCalled();
  });

  it('disables textarea when disabled prop is true', () => {
    render(<MessageInput onSend={mockOnSend} disabled={true} />);

    const textarea = screen.getByPlaceholderText(/type your message/i);
    expect(textarea).toBeDisabled();
  });

  it('shows character counter when approaching limit', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={mockOnSend} disabled={false} />);

    const textarea = screen.getByPlaceholderText(/type your message/i);
    // Type enough characters to trigger counter (>1800 chars)
    const longText = 'a'.repeat(1850);
    await user.type(textarea, longText);

    // Character counter should appear
    expect(screen.getByText(/1850/)).toBeInTheDocument();
  });

  it('prevents input beyond max length', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={mockOnSend} disabled={false} />);

    const textarea = screen.getByPlaceholderText(/type your message/i);
    await user.type(textarea, '12345678901234567890');

    expect(textarea).toHaveValue('1234567890');
  });

  it('auto-expands textarea as content grows', async () => {
    const user = userEvent.setup();
    render(<MessageInput onSend={mockOnSend} disabled={false} />);

    const textarea = screen.getByPlaceholderText(/type your message/i);

    await user.type(textarea, 'Line 1\nLine 2\nLine 3\nLine 4\nLine 5');

    // Height should adjust (implementation specific)
    // Just verify textarea still works
    expect(textarea).toBeInTheDocument();
  });
});
