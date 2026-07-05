import { cn } from "@/lib/utils";
import { Loader2 } from "lucide-react";

export function Spinner({ className }) {
  return <Loader2 className={cn("animate-spin text-primary", className)} />;
}

export function Loading({ label = "Cargando..." }) {
  return (
    <div className="flex items-center gap-3 text-muted-foreground py-16 justify-center">
      <Spinner className="h-5 w-5" /> <span className="text-sm">{label}</span>
    </div>
  );
}

export function ErrorState({ message }) {
  return (
    <div className="rounded-xl border border-[hsl(var(--loss)/0.3)] bg-[hsl(var(--loss)/0.08)] p-4 text-sm text-[hsl(var(--loss))]">
      {message || "Ha ocurrido un error."}
    </div>
  );
}

export function Empty({ title, hint }) {
  return (
    <div className="text-center py-16">
      <p className="text-foreground font-medium">{title}</p>
      {hint && <p className="text-sm text-muted-foreground mt-1">{hint}</p>}
    </div>
  );
}
