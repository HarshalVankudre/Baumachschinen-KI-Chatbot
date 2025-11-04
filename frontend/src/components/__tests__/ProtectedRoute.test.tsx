import { render, screen } from '@/test-utils/test-utils';
import { ProtectedRoute } from '../ProtectedRoute';
import { mockUser, mockAdminUser, mockSuperuser } from '@/test-utils/test-utils';
import { useAuthStore } from '@/store/authStore';

// Mock the auth store
jest.mock('@/store/authStore');

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('renders children when user is authenticated', () => {
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
    });

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('redirects to login when user is not authenticated', () => {
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      user: null,
      isAuthenticated: false,
    });

    render(
      <ProtectedRoute>
        <div>Protected Content</div>
      </ProtectedRoute>
    );

    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });

  it('allows access when user has required authorization level', () => {
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      user: mockAdminUser,
      isAuthenticated: true,
    });

    render(
      <ProtectedRoute requiredLevel={['admin']}>
        <div>Admin Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByText('Admin Content')).toBeInTheDocument();
  });

  it('denies access when user lacks required authorization level', () => {
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
    });

    render(
      <ProtectedRoute requiredLevel={['admin']}>
        <div>Admin Content</div>
      </ProtectedRoute>
    );

    expect(screen.queryByText('Admin Content')).not.toBeInTheDocument();
  });

  it('allows access when user has any of the required authorization levels', () => {
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      user: mockSuperuser,
      isAuthenticated: true,
    });

    render(
      <ProtectedRoute requiredLevel={['superuser', 'admin']}>
        <div>Privileged Content</div>
      </ProtectedRoute>
    );

    expect(screen.getByText('Privileged Content')).toBeInTheDocument();
  });
});
