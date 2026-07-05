import { cn } from "@/lib/utils";
export function Input({ className, ...props }) {
  return (
    <input
      className={cn("flex h-9 w-full rounded-lg border border-input bg-secondary/40 px-3 py-1 text-sm placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring", className)}
      {...props}
    />
  );
}
export function Select({ className, children, ...props }) {
  return (
    <select className={cn("flex h-9 w-full rounded-lg border border-input bg-secondary/40 px-3 text-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring", className)} {...props}>
      {children}
    </select>
  );
}
