import { cn } from "@/lib/utils"

interface LoadingSpinnerProps {
  size?: "sm" | "md" | "lg"
  className?: string
}

export function LoadingSpinner({ size = "md", className }: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: "h-5 w-5 border-2",
    md: "h-10 w-10 border-3",
    lg: "h-14 w-14 border-4",
  }

  return (
    <div className={cn("relative inline-flex items-center justify-center", className)}>
      <div
        className={cn(
          "animate-spin rounded-full border-primary/30 border-t-primary",
          sizeClasses[size],
        )}
        role="status"
        aria-label="Loading"
        style={{
          animation: "spin 0.8s cubic-bezier(0.4, 0, 0.2, 1) infinite"
        }}
      >
        <span className="sr-only">Loading...</span>
      </div>
      <div
        className={cn(
          "absolute rounded-full bg-primary/10 animate-pulse-subtle",
          size === "sm" && "h-3 w-3",
          size === "md" && "h-6 w-6",
          size === "lg" && "h-10 w-10"
        )}
      />
    </div>
  )
}
