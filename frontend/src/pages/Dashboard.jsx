import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { fmtMoney, fmtPct, pnlColor, cn } from "@/lib/utils";
import { PageHeader, StatCard, CHART_COLORS, SentimentBadge } from "@/components/shared";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Loading, ErrorState, Empty } from "@/components/ui/misc";
import { Badge } from "@/components/ui/badge";
import { Link } from "react-router-dom";
import { Wallet, TrendingUp, Coins, PiggyBank } from "lucide-react";
import {
  AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
  PieChart, Pie, Cell,
} from "recharts";

export default function Dashboard() {
  const pf = useApi(() => api.portfolio(), []);
  const hist = useApi(() => api.history(180), []);
  const events = useApi(() => api.alertEvents(false), []);

  if (pf.loading) return <Loading label="Cargando cartera..." />;
  if (pf.error) return <ErrorState message={pf.error} />;

  const s = pf.data.summary;
  const holdings = pf.data.holdings || [];
  const empty = holdings.length === 0;

  const movers = [...holdings].filter(h => h.pnl_pct).sort((a, b) => Math.abs(b.pnl_pct) - Math.abs(a.pnl_pct)).slice(0, 5);
  const alloc = pf.data.allocation.by_kind.map((a, i) => ({ ...a, fill: CHART_COLORS[i % CHART_COLORS.length] }));

  return (
    <>
      <PageHeader title="Dashboard" subtitle="Resumen de tu cartera, evolución y señales recientes." />

      {empty ? (
        <Card><CardContent>
          <Empty title="Aún no tienes posiciones" hint="Importa tu cartera de MyInvestor o añade posiciones manualmente para empezar." />
          <div className="flex justify-center gap-3">
            <Link to="/importar" className="text-primary text-sm font-medium hover:underline">Importar de MyInvestor →</Link>
            <Link to="/cartera" className="text-primary text-sm font-medium hover:underline">Añadir manual →</Link>
          </div>
        </CardContent></Card>
      ) : (
        <>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
            <StatCard label="Valor total" value={fmtMoney(s.total_value, s.base_currency)} icon={Wallet} />
            <StatCard label="Invertido" value={fmtMoney(s.total_invested, s.base_currency)} icon={PiggyBank}
              accent="bg-blue-500/15 text-blue-400" />
            <StatCard label="P&L total" value={fmtMoney(s.total_pnl, s.base_currency)} delta={s.total_pnl_pct}
              icon={TrendingUp} accent={cn(s.total_pnl >= 0 ? "bg-[hsl(var(--gain)/0.15)] text-[hsl(var(--gain))]" : "bg-[hsl(var(--loss)/0.15)] text-[hsl(var(--loss))]")} />
            <StatCard label="Posiciones" value={s.positions} sub={`${alloc.length} clases de activo`} icon={Coins}
              accent="bg-purple-500/15 text-purple-400" />
          </div>

          <div className="grid lg:grid-cols-3 gap-6 mb-6">
            <Card className="lg:col-span-2">
              <CardHeader><CardTitle>Evolución del valor (6 meses)</CardTitle></CardHeader>
              <CardContent>
                {hist.data && hist.data.length > 1 ? (
                  <ResponsiveContainer width="100%" height={260}>
                    <AreaChart data={hist.data}>
                      <defs>
                        <linearGradient id="g" x1="0" y1="0" x2="0" y2="1">
                          <stop offset="5%" stopColor="#2dd4bf" stopOpacity={0.4} />
                          <stop offset="95%" stopColor="#2dd4bf" stopOpacity={0} />
                        </linearGradient>
                      </defs>
                      <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={false} minTickGap={40} />
                      <YAxis tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={false} width={50}
                        tickFormatter={(v) => `${(v / 1000).toFixed(1)}k`} />
                      <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1e293b", borderRadius: 10 }}
                        formatter={(v) => fmtMoney(v, s.base_currency)} />
                      <Area type="monotone" dataKey="value" stroke="#2dd4bf" strokeWidth={2} fill="url(#g)" />
                    </AreaChart>
                  </ResponsiveContainer>
                ) : (
                  <Empty title="Sin histórico todavía" hint="Se irá registrando un punto por día según el backend refresque precios." />
                )}
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Distribución por activo</CardTitle></CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie data={alloc} dataKey="value" nameKey="label" innerRadius={55} outerRadius={85} paddingAngle={3}>
                      {alloc.map((a, i) => <Cell key={i} fill={a.fill} stroke="none" />)}
                    </Pie>
                    <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1e293b", borderRadius: 10 }}
                      formatter={(v) => fmtMoney(v, s.base_currency)} />
                  </PieChart>
                </ResponsiveContainer>
                <div className="space-y-1.5 mt-2">
                  {alloc.map((a, i) => (
                    <div key={i} className="flex items-center justify-between text-sm">
                      <span className="flex items-center gap-2"><span className="h-2.5 w-2.5 rounded-sm" style={{ background: a.fill }} />{a.label}</span>
                      <span className="num text-muted-foreground">{fmtMoney(a.value, s.base_currency, 0)}</span>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          <div className="grid lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader><CardTitle>Mayores movimientos (P&L)</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {movers.length === 0 ? <Empty title="Sin datos de P&L" /> : movers.map((h) => (
                  <div key={h.asset_id} className="flex items-center justify-between py-1.5">
                    <div>
                      <div className="font-medium text-sm">{h.symbol || h.name}</div>
                      <div className="text-xs text-muted-foreground">{fmtMoney(h.market_value, h.currency)}</div>
                    </div>
                    <span className={cn("num font-semibold", pnlColor(h.pnl_pct))}>{fmtPct(h.pnl_pct)}</span>
                  </div>
                ))}
              </CardContent>
            </Card>

            <Card>
              <CardHeader><CardTitle>Alertas recientes</CardTitle></CardHeader>
              <CardContent className="space-y-2">
                {!events.data || events.data.length === 0 ? (
                  <Empty title="Sin alertas disparadas" hint="Configura alertas en la sección Alertas." />
                ) : events.data.slice(0, 6).map((e) => (
                  <div key={e.id} className="flex items-start gap-2 py-1.5 text-sm">
                    <Badge tone={e.read ? "neutral" : "primary"} className="mt-0.5">{e.read ? "leída" : "nueva"}</Badge>
                    <div>
                      <div>{e.message}</div>
                      <div className="text-xs text-muted-foreground">{new Date(e.triggered_at).toLocaleString("es-ES")}</div>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </div>
        </>
      )}
    </>
  );
}
