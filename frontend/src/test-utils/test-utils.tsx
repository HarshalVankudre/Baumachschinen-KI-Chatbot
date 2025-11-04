import type { ReactElement, ReactNode } from 'react';
import { render, type RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';

// Create a custom render function that includes all providers
interface AllTheProvidersProps {
  children: ReactNode;
}

function AllTheProviders({ children }: AllTheProvidersProps) {
  // Create a new QueryClient for each test to ensure isolation
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false, // Don't retry in tests
        gcTime: Infinity, // Keep cache forever in tests
      },
      mutations: {
        retry: false,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>{children}</BrowserRouter>
    </QueryClientProvider>
  );
}

interface CustomRenderOptions extends Omit<RenderOptions, 'wrapper'> {
  initialRoute?: string;
}

function customRender(
  ui: ReactElement,
  options?: CustomRenderOptions
): ReturnType<typeof render> {
  const { initialRoute = '/', ...renderOptions } = options || {};

  // Set initial route if provided
  if (initialRoute !== '/') {
    window.history.pushState({}, 'Test page', initialRoute);
  }

  return render(ui, { wrapper: AllTheProviders, ...renderOptions });
}

// Re-export everything from React Testing Library
export * from '@testing-library/react';
export { customRender as render };

// Helper function to wait for async operations
export const waitForLoadingToFinish = () => {
  return new Promise((resolve) => setTimeout(resolve, 0));
};

// Mock user for tests
export const mockUser = {
  user_id: 'test-user-id',
  username: 'testuser',
  email: 'test@example.com',
  authorization_level: 'regular' as const,
  created_at: '2024-01-01T00:00:00Z',
  email_verified: true,
  account_status: 'approved' as const,
};

export const mockAdminUser = {
  user_id: 'admin-user-id',
  username: 'adminuser',
  email: 'admin@example.com',
  authorization_level: 'admin' as const,
  created_at: '2024-01-01T00:00:00Z',
  email_verified: true,
  account_status: 'approved' as const,
};

export const mockSuperuser = {
  user_id: 'superuser-id',
  username: 'superuser',
  email: 'super@example.com',
  authorization_level: 'superuser' as const,
  created_at: '2024-01-01T00:00:00Z',
  email_verified: true,
  account_status: 'approved' as const,
};
