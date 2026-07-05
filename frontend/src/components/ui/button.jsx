import { cn } from "@/lib/utils";
const variants = {
  default: "bg-primary text-primary-foreground hover:opacity-90",
  outline: "border border-border bg-transparent hover:bg-secondary",
  ghost: "hover:bg-secondary text-foreground",
  destructive: "bg-[hsl(var(--loss))] text-white hover:opacity-90",
  secondary: "bg-secondary text-secondary-foreground hover:opacity-80",
};
const sizes = { default: "h-9 px-4 text-sm", sm: "h-8 px-3 text-xs", icon: "h-9 w-9", lg: "h-11 px-6" };
export function Button({ className, variant = "default", size = "default", ...props }) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-all disabled:opacity-50 disabled:pointer-events-none focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
        variants[variant], sizes[size], className
      )}
      {...props}
    />
  );
}
