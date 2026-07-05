import { cn } from "@/lib/utils";
export function Card({ className, ...props }) {
  return <div className={cn("glass rounded-xl shadow-lg shadow-black/20", className)} {...props} />;
}
export function CardHeader({ className, ...props }) {
  return <div className={cn("flex flex-col space-y-1 p-5 pb-2", className)} {...props} />;
}
export function CardTitle({ className, ...props }) {
  return <h3 className={cn("text-sm font-semibold text-muted-foreground tracking-wide uppercase", className)} {...props} />;
}
export function CardContent({ className, ...props }) {
  return <div className={cn("p-5 pt-2", className)} {...props} />;
}
