import { useState, useMemo } from 'react';
import { Input } from '@/components/ui/input';
import { Eye, EyeOff } from 'lucide-react';
import { cn } from '@/lib/utils';

interface PasswordInputProps {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  className?: string;
  showStrengthMeter?: boolean;
  disabled?: boolean;
  id?: string;
  autoComplete?: string;
}

type PasswordStrength = 'weak' | 'medium' | 'strong' | null;

function calculatePasswordStrength(password: string): PasswordStrength {
  if (!password) return null;

  let score = 0;

  // Length check
  if (password.length >= 8) score++;
  if (password.length >= 12) score++;

  // Character variety
  if (/[a-z]/.test(password)) score++;
  if (/[A-Z]/.test(password)) score++;
  if (/[0-9]/.test(password)) score++;
  if (/[^a-zA-Z0-9]/.test(password)) score++;

  if (score <= 2) return 'weak';
  if (score <= 4) return 'medium';
  return 'strong';
}

export function PasswordInput({
  value,
  onChange,
  placeholder = 'Enter password',
  className,
  showStrengthMeter = false,
  disabled = false,
  id,
  autoComplete,
}: PasswordInputProps) {
  const [showPassword, setShowPassword] = useState(false);

  const strength = useMemo(() => calculatePasswordStrength(value), [value]);

  const strengthConfig = {
    weak: {
      label: 'Schwach',
      color: 'bg-destructive',
      width: 'w-1/3',
    },
    medium: {
      label: 'Mittel',
      color: 'bg-yellow-500',
      width: 'w-2/3',
    },
    strong: {
      label: 'Stark',
      color: 'bg-green-500',
      width: 'w-full',
    },
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    onChange(e.target.value);
  };

  const toggleShowPassword = () => {
    setShowPassword(!showPassword);
  };

  return (
    <div className={cn('space-y-2', className)}>
      <div className="relative">
        <Input
          id={id}
          type={showPassword ? 'text' : 'password'}
          value={value}
          onChange={handleChange}
          placeholder={placeholder}
          disabled={disabled}
          autoComplete={autoComplete}
          className="pr-10"
          aria-label="Password"
        />
        <button
          type="button"
          onClick={toggleShowPassword}
          disabled={disabled}
          className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors disabled:opacity-50"
          aria-label={showPassword ? 'Hide password' : 'Show password'}
        >
          {showPassword ? (
            <EyeOff className="h-4 w-4" />
          ) : (
            <Eye className="h-4 w-4" />
          )}
        </button>
      </div>

      {showStrengthMeter && value && strength && (
        <div className="space-y-1" role="status" aria-live="polite">
          <div className="flex items-center justify-between text-xs">
            <span className="text-muted-foreground">Passwortstärke:</span>
            <span
              className={cn(
                'font-medium',
                strength === 'weak' && 'text-destructive',
                strength === 'medium' && 'text-yellow-600',
                strength === 'strong' && 'text-green-600'
              )}
            >
              {strengthConfig[strength].label}
            </span>
          </div>
          <div className="h-2 w-full bg-muted rounded-full overflow-hidden">
            <div
              className={cn(
                'h-full transition-all duration-300',
                strengthConfig[strength].color,
                strengthConfig[strength].width
              )}
              aria-label={`Passwortstärke: ${strengthConfig[strength].label}`}
            />
          </div>
          {strength === 'weak' && (
            <p className="text-xs text-muted-foreground">
              Verwenden Sie 8+ Zeichen mit Groß-/Kleinschreibung, Zahlen und Symbolen
            </p>
          )}
        </div>
      )}
    </div>
  );
}
