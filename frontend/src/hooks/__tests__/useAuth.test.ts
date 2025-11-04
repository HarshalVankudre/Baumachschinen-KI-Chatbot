import { renderHook, waitFor } from '@/test-utils/test-utils';
import { useAuth } from '../useAuth';
import { useAuthStore } from '@/store/authStore';

jest.mock('@/store/authStore');

describe('useAuth', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('returns user and authentication status', () => {
    const mockUser = {
      user_id: '1',
      username: 'testuser',
      email: 'test@example.com',
      authorization_level: 'regular' as const,
    };

    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      user: mockUser,
      isAuthenticated: true,
      login: jest.fn(),
      logout: jest.fn(),
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.user).toEqual(mockUser);
    expect(result.current.isAuthenticated).toBe(true);
  });

  it('returns null user when not authenticated', () => {
    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
    });

    const { result } = renderHook(() => useAuth());

    expect(result.current.user).toBeNull();
    expect(result.current.isAuthenticated).toBe(false);
  });

  it('provides login function', () => {
    const mockLogin = jest.fn();

    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      user: null,
      isAuthenticated: false,
      login: mockLogin,
      logout: jest.fn(),
    });

    const { result } = renderHook(() => useAuth());

    expect(typeof result.current.login).toBe('function');
  });

  it('provides logout function', () => {
    const mockLogout = jest.fn();

    (useAuthStore as unknown as jest.Mock).mockReturnValue({
      user: { user_id: '1', username: 'test' },
      isAuthenticated: true,
      login: jest.fn(),
      logout: mockLogout,
    });

    const { result } = renderHook(() => useAuth());

    expect(typeof result.current.logout).toBe('function');
  });

  it('updates when auth state changes', async () => {
    const mockUser = {
      user_id: '1',
      username: 'testuser',
      email: 'test@example.com',
      authorization_level: 'regular' as const,
    };

    let mockAuthState = {
      user: null,
      isAuthenticated: false,
      login: jest.fn(),
      logout: jest.fn(),
    };

    (useAuthStore as unknown as jest.Mock).mockImplementation(() => mockAuthState);

    const { result, rerender } = renderHook(() => useAuth());

    expect(result.current.isAuthenticated).toBe(false);

    // Simulate login
    mockAuthState = {
      user: mockUser,
      isAuthenticated: true,
      login: jest.fn(),
      logout: jest.fn(),
    };

    rerender();

    await waitFor(() => {
      expect(result.current.isAuthenticated).toBe(true);
    });
  });
});
