import { render, screen, waitFor } from '@/test-utils/test-utils';
import userEvent from '@testing-library/user-event';
import { PendingApprovalsTab } from '../PendingApprovalsTab';
import * as adminService from '@/services/adminService';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Mock the api service to avoid import.meta issues in Jest
jest.mock('@/services/api');
jest.mock('@/services/adminService');

const mockPendingUsers = [
  {
    user_id: '1',
    username: 'testuser1',
    email: 'test1@example.com',
    created_at: '2024-01-01T00:00:00Z',
    email_verified: true,
  },
  {
    user_id: '2',
    username: 'testuser2',
    email: 'test2@example.com',
    created_at: '2024-01-02T00:00:00Z',
    email_verified: false,
  },
];

describe('PendingApprovalsTab', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (adminService.adminService.getPendingUsers as jest.Mock).mockResolvedValue(mockPendingUsers);
  });

  const renderWithQuery = (ui: React.ReactElement) => {
    const queryClient = new QueryClient({
      defaultOptions: { queries: { retry: false } },
    });
    return render(
      <QueryClientProvider client={queryClient}>{ui}</QueryClientProvider>
    );
  };

  it('renders pending users table', async () => {
    renderWithQuery(<PendingApprovalsTab />);

    await waitFor(() => {
      expect(screen.getByText('testuser1')).toBeInTheDocument();
      expect(screen.getByText('testuser2')).toBeInTheDocument();
    });
  });

  it('displays email verification status', async () => {
    renderWithQuery(<PendingApprovalsTab />);

    await waitFor(() => {
      const checkmarks = screen.getAllByText('✓');
      const crosses = screen.getAllByText('✗');
      expect(checkmarks.length).toBeGreaterThan(0);
      expect(crosses.length).toBeGreaterThan(0);
    });
  });

  it('shows approve and reject buttons for each user', async () => {
    renderWithQuery(<PendingApprovalsTab />);

    await waitFor(() => {
      const approveButtons = screen.getAllByRole('button', { name: /approve/i });
      const rejectButtons = screen.getAllByRole('button', { name: /reject/i });

      expect(approveButtons.length).toBe(2);
      expect(rejectButtons.length).toBe(2);
    });
  });

  it('opens authorization selection dialog on approve click', async () => {
    const user = userEvent.setup();
    renderWithQuery(<PendingApprovalsTab />);

    await waitFor(() => {
      expect(screen.getByText('testuser1')).toBeInTheDocument();
    });

    const approveButtons = screen.getAllByRole('button', { name: /approve/i });
    await user.click(approveButtons[0]);

    await waitFor(() => {
      expect(screen.getByText(/select authorization level/i)).toBeInTheDocument();
    });
  });

  it('approves user with selected authorization level', async () => {
    const user = userEvent.setup();
    (adminService.adminService.approveUser as jest.Mock).mockResolvedValue({});

    renderWithQuery(<PendingApprovalsTab />);

    await waitFor(() => {
      expect(screen.getByText('testuser1')).toBeInTheDocument();
    });

    const approveButtons = screen.getAllByRole('button', { name: /approve/i });
    await user.click(approveButtons[0]);

    await waitFor(() => {
      expect(screen.getByText(/regular/i)).toBeInTheDocument();
    });

    // Select Regular authorization
    const regularOption = screen.getByText(/regular/i);
    await user.click(regularOption);

    // Confirm approval
    const confirmButton = screen.getByRole('button', { name: /confirm/i });
    await user.click(confirmButton);

    await waitFor(() => {
      expect(adminService.adminService.approveUser).toHaveBeenCalledWith('1', 'regular');
    });
  });

  it('opens rejection dialog on reject click', async () => {
    const user = userEvent.setup();
    renderWithQuery(<PendingApprovalsTab />);

    await waitFor(() => {
      expect(screen.getByText('testuser1')).toBeInTheDocument();
    });

    const rejectButtons = screen.getAllByRole('button', { name: /reject/i });
    await user.click(rejectButtons[0]);

    await waitFor(() => {
      expect(screen.getByText(/reject user/i)).toBeInTheDocument();
    });
  });

  it('rejects user with optional reason', async () => {
    const user = userEvent.setup();
    (adminService.adminService.rejectUser as jest.Mock).mockResolvedValue({});

    renderWithQuery(<PendingApprovalsTab />);

    await waitFor(() => {
      expect(screen.getByText('testuser1')).toBeInTheDocument();
    });

    const rejectButtons = screen.getAllByRole('button', { name: /reject/i });
    await user.click(rejectButtons[0]);

    await waitFor(() => {
      const reasonInput = screen.getByLabelText(/reason/i);
      expect(reasonInput).toBeInTheDocument();
    });

    const reasonInput = screen.getByLabelText(/reason/i);
    await user.type(reasonInput, 'Invalid application');

    const confirmButton = screen.getByRole('button', { name: /confirm|reject/i });
    await user.click(confirmButton);

    await waitFor(() => {
      expect(adminService.adminService.rejectUser).toHaveBeenCalledWith('1', 'Invalid application');
    });
  });

  it('shows empty state when no pending users', async () => {
    (adminService.adminService.getPendingUsers as jest.Mock).mockResolvedValue([]);

    renderWithQuery(<PendingApprovalsTab />);

    await waitFor(() => {
      expect(screen.getByText(/no pending approvals/i)).toBeInTheDocument();
    });
  });

  it('displays loading state while fetching', () => {
    (adminService.adminService.getPendingUsers as jest.Mock).mockImplementation(
      () => new Promise(() => {}) // Never resolves
    );

    renderWithQuery(<PendingApprovalsTab />);

    expect(screen.getByRole('status')).toBeInTheDocument();
  });

  it('displays error message on fetch failure', async () => {
    (adminService.adminService.getPendingUsers as jest.Mock).mockRejectedValue(
      new Error('Failed to fetch')
    );

    renderWithQuery(<PendingApprovalsTab />);

    await waitFor(() => {
      expect(screen.getByText(/error/i)).toBeInTheDocument();
    });
  });
});
