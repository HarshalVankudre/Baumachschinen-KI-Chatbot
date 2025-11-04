import { useState, useEffect, useCallback } from 'react';

/**
 * Custom hook for persisting state to localStorage with cross-tab synchronization
 */
export function useLocalStorage<T>(
  key: string,
  initialValue: T
): [T, (value: T | ((val: T) => T)) => void, () => void] {
  // Get stored value from localStorage or use initial value
  const readValue = useCallback((): T => {
    if (typeof window === 'undefined') {
      return initialValue;
    }

    try {
      const item = window.localStorage.getItem(key);
      return item ? (JSON.parse(item) as T) : initialValue;
    } catch (error) {
      console.warn(`Error reading localStorage key "${key}":`, error);
      return initialValue;
    }
  }, [initialValue, key]);

  const [storedValue, setStoredValue] = useState<T>(readValue);

  // Set value in localStorage and state
  const setValue = useCallback(
    (value: T | ((val: T) => T)) => {
      if (typeof window === 'undefined') {
        console.warn(
          `Tried setting localStorage key "${key}" even though environment is not a client`
        );
        return;
      }

      try {
        const newValue = value instanceof Function ? value(storedValue) : value;

        window.localStorage.setItem(key, JSON.stringify(newValue));
        setStoredValue(newValue);

        // Dispatch custom event for cross-tab synchronization
        window.dispatchEvent(
          new CustomEvent('local-storage', {
            detail: { key, value: newValue },
          })
        );
      } catch (error) {
        console.warn(`Error setting localStorage key "${key}":`, error);
      }
    },
    [key, storedValue]
  );

  // Remove value from localStorage
  const removeValue = useCallback(() => {
    if (typeof window === 'undefined') {
      console.warn(
        `Tried removing localStorage key "${key}" even though environment is not a client`
      );
      return;
    }

    try {
      window.localStorage.removeItem(key);
      setStoredValue(initialValue);

      window.dispatchEvent(
        new CustomEvent('local-storage', {
          detail: { key, value: null },
        })
      );
    } catch (error) {
      console.warn(`Error removing localStorage key "${key}":`, error);
    }
  }, [key, initialValue]);

  // Listen for changes in localStorage (cross-tab synchronization)
  useEffect(() => {
    const handleStorageChange = (e: StorageEvent | CustomEvent) => {
      if ('key' in e && e.key && e.key !== key) {
        return;
      }

      if ('detail' in e && e.detail && e.detail.key !== key) {
        return;
      }

      setStoredValue(readValue());
    };

    // Listen to both storage event (other tabs) and custom event (same tab)
    window.addEventListener('storage', handleStorageChange as EventListener);
    window.addEventListener('local-storage', handleStorageChange as EventListener);

    return () => {
      window.removeEventListener('storage', handleStorageChange as EventListener);
      window.removeEventListener('local-storage', handleStorageChange as EventListener);
    };
  }, [key, readValue]);

  return [storedValue, setValue, removeValue];
}
