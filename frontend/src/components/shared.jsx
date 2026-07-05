import { cn, fmtPct, pnlColor } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { ArrowDownRight, ArrowUpRight } from "lucide-react";

export function PageHeader({ title, subtitle, children }) {
  return (
    <div className="flex flex-wrap items-end justify-between gap-4 mb-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight">{title}</h1>
        {subtitle && <p className="text-sm text-muted-foreground mt-1 max-w-2xl">{subtitle}</p>}
      </div>
      {children && <div className="flex items-center gap-2">{children}</div>}
    </div>
  );
}

export function StatCard({ label, value, sub, delta, icon: Icon, accent }) {
  return (
    <div className="glass rounded-xl p-5 relative overflow-hidden">
      {Icon && (
        <div className={cn("absolute right-4 top-4 h-9 w-9 rounded-lg flex items-center justify-center",
          accent || "bg-primary/15 text-primary")}>
          <Icon className="h-5 w-5" />
        </div>
      )}
      <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className="text-2xl font-bold num mt-2">{value}</div>
      {(sub || delta !== undefined) && (
        <div className="flex items-center gap-2 mt-1 text-sm">
          {delta !== undefined && delta !== null && (
            <span className={cn("flex items-center gap-0.5 font-medium num", pnlColor(delta))}>
              {delta >= 0 ? <ArrowUpRight className="h-3.5 w-3.5" /> : <ArrowDownRight className="h-3.5 w-3.5" />}
              {fmtPct(delta)}
            </span>
          )}
          {sub && <span className="text-muted-foreground num">{sub}</span>}
        </div>
      )}
    </div>
  );
}

export function SentimentBadge({ sentiment }) {
  if (!sentiment) return null;
  const map = {
    positive: { tone: "gain", label: "Positivo" },
    negative: { tone: "loss", label: "Negativo" },
    neutral: { tone: "neutral", label: "Neutro" },
  };
  const m = map[sentiment.label] || map.neutral;
  return <Badge tone={m.tone}>{m.label}</Badge>;
}

export const CHART_COLORS = ["#2dd4bf", "#3b82f6", "#a855f7", "#f59e0b", "#ec4899", "#10b981", "#6366f1", "#ef4444"];
