import { useState, useEffect } from 'react';
import { Input } from '@/components/ui/input';
import { X, Search } from 'lucide-react';
import { useDebounce } from '@/hooks/useDebounce';
import { cn } from '@/lib/utils';

interface SearchInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  debounceMs?: number;
  onDebouncedChange?: (value: string) => void;
}

export function SearchInput({
  value,
  onChange,
  placeholder = 'Suchen...',
  className,
  debounceMs = 300,
  onDebouncedChange,
}: SearchInputProps) {
  const [internalValue, setInternalValue] = useState(value);
  const debouncedValue = useDebounce(internalValue, debounceMs);

  useEffect(() => {
    setInternalValue(value);
  }, [value]);

  useEffect(() => {
    if (onDebouncedChange) {
      onDebouncedChange(debouncedValue);
    }
  }, [debouncedValue, onDebouncedChange]);

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const newValue = e.target.value;
    setInternalValue(newValue);
    onChange(newValue);
  };

  const handleClear = () => {
    setInternalValue('');
    onChange('');
    if (onDebouncedChange) {
      onDebouncedChange('');
    }
  };

  return (
    <div className={cn('relative', className)}>
      <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground pointer-events-none" />
      <Input
        type="text"
        value={internalValue}
        onChange={handleChange}
        placeholder={placeholder}
        className="pl-10 pr-10"
        aria-label="Search"
      />
      {internalValue && (
        <button
          type="button"
          onClick={handleClear}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
          aria-label="Clear search"
        >
          <X className="h-4 w-4" />
        </button>
      )}
    </div>
  );
}
