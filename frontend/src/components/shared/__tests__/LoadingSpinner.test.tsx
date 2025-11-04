import { render, screen } from '@/test-utils/test-utils';
import { LoadingSpinner } from '../LoadingSpinner';

describe('LoadingSpinner', () => {
  it('renders with default size', () => {
    render(<LoadingSpinner />);

    const spinner = screen.getByRole('status');
    expect(spinner).toBeInTheDocument();
    expect(spinner).toHaveAttribute('aria-label', 'Loading');
  });

  it('renders with small size', () => {
    render(<LoadingSpinner size="sm" />);

    const spinner = screen.getByRole('status');
    expect(spinner).toBeInTheDocument();
  });

  it('renders with large size', () => {
    render(<LoadingSpinner size="lg" />);

    const spinner = screen.getByRole('status');
    expect(spinner).toBeInTheDocument();
  });

  it('renders with custom className', () => {
    render(<LoadingSpinner className="custom-class" />);

    const spinner = screen.getByRole('status');
    expect(spinner).toHaveClass('custom-class');
  });
});
