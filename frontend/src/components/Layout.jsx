import { NavLink, useLocation } from "react-router-dom";
import {
  LayoutDashboard, Wallet, Newspaper, LineChart, Bell, FlaskConical,
  Upload, Star, TrendingUp, RefreshCw, Gauge, Sparkles,
} from "lucide-react";
import { useEffect, useState } from "react";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";

const nav = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/cartera", label: "Cartera", icon: Wallet },
  { to: "/watchlist", label: "Watchlist", icon: Star },
  { to: "/noticias", label: "Noticias", icon: Newspaper },
  { to: "/analisis", label: "Análisis", icon: LineChart },
  { to: "/rendimiento", label: "Rendimiento", icon: Gauge },
  { to: "/sugerencias", label: "Sugerencias", icon: Sparkles },
  { to: "/alertas", label: "Alertas", icon: Bell },
  { to: "/research", label: "Research", icon: FlaskConical },
  { to: "/importar", label: "Importar", icon: Upload },
];

export default function Layout({ children }) {
  const [unread, setUnread] = useState(0);
  const [status, setStatus] = useState(null);
  const loc = useLocation();

  useEffect(() => {
    api.alertEvents(true).then((e) => setUnread(e.length || 0)).catch(() => {});
    api.status().then(setStatus).catch(() => {});
  }, [loc.pathname]);

  return (
    <div className="min-h-screen flex">
      <aside className="w-60 shrink-0 border-r border-border/60 bg-[hsl(var(--card)/0.4)] backdrop-blur-xl hidden md:flex flex-col fixed h-screen">
        <div className="px-5 h-16 flex items-center gap-2.5 border-b border-border/60">
          <div className="h-9 w-9 rounded-lg bg-gradient-to-br from-primary to-[hsl(217_90%_55%)] flex items-center justify-center">
            <TrendingUp className="h-5 w-5 text-primary-foreground" />
          </div>
          <div className="leading-tight">
            <div className="font-bold text-[15px]">Market Hub</div>
            <div className="text-[10px] text-muted-foreground uppercase tracking-wider">OpenBB · Personal</div>
          </div>
        </div>
        <nav className="flex-1 p-3 space-y-1 overflow-y-auto">
          {nav.map((n) => (
            <NavLink
              key={n.to} to={n.to} end={n.end}
              className={({ isActive }) => cn(
                "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-all",
                isActive ? "bg-primary/15 text-primary" : "text-muted-foreground hover:text-foreground hover:bg-secondary/50"
              )}
            >
              <n.icon className="h-[18px] w-[18px]" />
              {n.label}
              {n.to === "/alertas" && unread > 0 && (
                <span className="ml-auto text-[10px] font-bold bg-[hsl(var(--loss))] text-white rounded-full px-1.5 py-0.5">{unread}</span>
              )}
            </NavLink>
          ))}
        </nav>
        <div className="p-3 border-t border-border/60 text-[11px] text-muted-foreground">
          <div className="flex items-center gap-2">
            <span className={cn("h-2 w-2 rounded-full", status?.openbb ? "bg-[hsl(var(--gain))]" : "bg-yellow-500")} />
            {status?.openbb ? "OpenBB conectado" : "OpenBB no detectado"}
          </div>
        </div>
      </aside>

      <main className="flex-1 md:ml-60">
        <header className="h-16 border-b border-border/60 bg-[hsl(var(--background)/0.7)] backdrop-blur-xl sticky top-0 z-20 flex items-center justify-between px-6">
          <div className="md:hidden font-bold flex items-center gap-2"><TrendingUp className="h-5 w-5 text-primary" /> Market Hub</div>
          <div className="hidden md:block text-sm text-muted-foreground">
            {new Date().toLocaleDateString("es-ES", { weekday: "long", day: "numeric", month: "long", year: "numeric" })}
          </div>
          <RefreshButton />
        </header>
        <div className="p-6 max-w-[1400px] mx-auto animate-fade">{children}</div>
      </main>
    </div>
  );
}

function RefreshButton() {
  const [busy, setBusy] = useState(false);
  const run = async () => {
    setBusy(true);
    try { await api.refreshPrices(); await api.checkAlerts(); window.location.reload(); }
    finally { setBusy(false); }
  };
  return (
    <Button variant="outline" size="sm" onClick={run} disabled={busy}>
      <RefreshCw className={cn("h-4 w-4", busy && "animate-spin")} />
      Actualizar
    </Button>
  );
}
