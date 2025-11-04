import { renderHook } from '@/test-utils/test-utils';
import { useDebounce } from '../useDebounce';
import { act } from 'react';

jest.useFakeTimers();

describe('useDebounce', () => {
  afterEach(() => {
    jest.clearAllTimers();
  });

  it('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebounce('initial', 500));

    expect(result.current).toBe('initial');
  });

  it('debounces value changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 500 },
      }
    );

    expect(result.current).toBe('initial');

    // Update value
    rerender({ value: 'updated', delay: 500 });

    // Value should not change immediately
    expect(result.current).toBe('initial');

    // Fast-forward time
    act(() => {
      jest.advanceTimersByTime(500);
    });

    // Value should now be updated
    expect(result.current).toBe('updated');
  });

  it('cancels previous timeout on rapid changes', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 500 },
      }
    );

    // Rapid updates
    rerender({ value: 'update1', delay: 500 });
    act(() => {
      jest.advanceTimersByTime(200);
    });

    rerender({ value: 'update2', delay: 500 });
    act(() => {
      jest.advanceTimersByTime(200);
    });

    rerender({ value: 'update3', delay: 500 });

    // Value should still be initial
    expect(result.current).toBe('initial');

    // Fast-forward full delay
    act(() => {
      jest.advanceTimersByTime(500);
    });

    // Only the last update should be applied
    expect(result.current).toBe('update3');
  });

  it('uses custom delay', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 1000 },
      }
    );

    rerender({ value: 'updated', delay: 1000 });

    act(() => {
      jest.advanceTimersByTime(500);
    });

    // Should not update after 500ms
    expect(result.current).toBe('initial');

    act(() => {
      jest.advanceTimersByTime(500);
    });

    // Should update after 1000ms
    expect(result.current).toBe('updated');
  });

  it('handles numeric values', () => {
    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 0, delay: 300 },
      }
    );

    expect(result.current).toBe(0);

    rerender({ value: 42, delay: 300 });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toBe(42);
  });

  it('handles object values', () => {
    const initialObj = { name: 'John' };
    const updatedObj = { name: 'Jane' };

    const { result, rerender } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: initialObj, delay: 300 },
      }
    );

    expect(result.current).toEqual(initialObj);

    rerender({ value: updatedObj, delay: 300 });

    act(() => {
      jest.advanceTimersByTime(300);
    });

    expect(result.current).toEqual(updatedObj);
  });

  it('cleans up timeout on unmount', () => {
    const { rerender, unmount } = renderHook(
      ({ value, delay }) => useDebounce(value, delay),
      {
        initialProps: { value: 'initial', delay: 500 },
      }
    );

    rerender({ value: 'updated', delay: 500 });

    unmount();

    // This should not throw any errors
    act(() => {
      jest.advanceTimersByTime(500);
    });
  });
});
