import { cn } from "@/lib/utils";
const tones = {
  default: "bg-secondary text-secondary-foreground",
  gain: "bg-[hsl(var(--gain)/0.15)] text-[hsl(var(--gain))] border border-[hsl(var(--gain)/0.3)]",
  loss: "bg-[hsl(var(--loss)/0.15)] text-[hsl(var(--loss))] border border-[hsl(var(--loss)/0.3)]",
  neutral: "bg-muted text-muted-foreground",
  primary: "bg-[hsl(var(--primary)/0.15)] text-[hsl(var(--primary))] border border-[hsl(var(--primary)/0.3)]",
};
export function Badge({ className, tone = "default", ...props }) {
  return <span className={cn("inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium", tones[tone], className)} {...props} />;
}
