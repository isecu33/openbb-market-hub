import { cn } from "@/lib/utils";
export function Table({ className, ...props }) {
  return <div className="w-full overflow-x-auto"><table className={cn("w-full text-sm border-collapse", className)} {...props} /></div>;
}
export function THead({ className, ...props }) {
  return <thead className={cn("text-xs uppercase text-muted-foreground", className)} {...props} />;
}
export function TR({ className, ...props }) {
  return <tr className={cn("border-b border-border/60 hover:bg-secondary/30 transition-colors", className)} {...props} />;
}
export function TH({ className, ...props }) {
  return <th className={cn("text-left font-medium px-3 py-2.5", className)} {...props} />;
}
export function TD({ className, ...props }) {
  return <td className={cn("px-3 py-2.5", className)} {...props} />;
}
