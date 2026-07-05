import { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { fmtMoney, fmtNum, fmtPct, pnlColor, cn } from "@/lib/utils";
import { PageHeader, StatCard } from "@/components/shared";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, THead, TR, TH, TD } from "@/components/ui/table";
import { Select } from "@/components/ui/input";
import { Loading, ErrorState, Empty } from "@/components/ui/misc";
import { Activity, TrendingDown, Gauge, Percent, Download } from "lucide-react";
import {
  LineChart, Line, AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer,
} from "recharts";

// Par de series validado para daltonismo/contraste sobre fondo oscuro
// (scripts/validate_palette.js del skill dataviz: ΔE deutan 62.9, contraste >3:1).
const COLOR_PORTFOLIO = "#0d9488";
const COLOR_BENCHMARK = "#3b82f6";
const COLOR_DRAWDOWN = "#ef4444";

const BENCHMARKS = [
  { value: "SPY", label: "S&P 500 (SPY)" },
  { value: "QQQ", label: "Nasdaq 100 (QQQ)" },
  { value: "URTH", label: "MSCI World (URTH)" },
];

const tooltipStyle = { background: "#0b1220", border: "1px solid #1e293b", borderRadius: 10 };

export default function Performance() {
  const [days, setDays] = useState(365);
  const [benchmark, setBenchmark] = useState("SPY");
  const m = useApi(() => api.metrics(days, benchmark), [days, benchmark]);

  if (m.loading) return <Loading label="Calculando métricas..." />;
  if (m.error) return <ErrorState message={m.error} />;

  const { returns = {}, concentration = {}, by_currency = [], income = {}, caveats = [] } = m.data;
  const bench = m.data.benchmark || {};
  const hasReturns = (returns.days_observed || 0) >= 2;

  return (
    <>
      <PageHeader title="Rendimiento" subtitle="Métricas de retorno y riesgo de la cartera, comparación con un índice y calidad de la diversificación.">
        <Select value={days} onChange={(e) => setDays(Number(e.target.value))} className="w-36">
          <option value={90}>3 meses</option>
          <option value={180}>6 meses</option>
          <option value={365}>1 año</option>
          <option value={730}>2 años</option>
        </Select>
        <Select value={benchmark} onChange={(e) => setBenchmark(e.target.value)} className="w-44">
          {BENCHMARKS.map((b) => <option key={b.value} value={b.value}>{b.label}</option>)}
        </Select>
        <a href="/api/portfolio/export/holdings.csv" download
          className="inline-flex items-center gap-1.5 text-sm text-primary hover:underline font-medium">
          <Download className="h-4 w-4" /> CSV
        </a>
      </PageHeader>

      {caveats.length > 0 && (
        <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-4 text-sm text-yellow-200/90 mb-6 space-y-1">
          {caveats.map((c, i) => <p key={i}>· {c}</p>)}
        </div>
      )}

      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
        <StatCard label="Retorno acumulado" icon={Percent}
          value={hasReturns ? fmtPct(returns.cumulative_pct) : "—"}
          sub={hasReturns ? `${returns.days_observed} días observados` : "sin histórico"} />
        <StatCard label="Volatilidad anualizada" icon={Activity}
          value={hasReturns ? fmtPct(returns.annualized_vol_pct) : "—"}
          accent="bg-blue-500/15 text-blue-400" />
        <StatCard label="Ratio de Sharpe" icon={Gauge}
          value={hasReturns && returns.sharpe !== null ? fmtNum(returns.sharpe) : "—"}
          accent="bg-purple-500/15 text-purple-400" />
        <StatCard label="Máx. drawdown" icon={TrendingDown}
          value={hasReturns ? fmtPct(returns.max_drawdown_pct) : "—"}
          sub={hasReturns && returns.worst_day ? `peor día ${fmtPct(returns.worst_day.pct)}` : undefined}
          accent="bg-[hsl(var(--loss)/0.15)] text-[hsl(var(--loss))]" />
      </div>

      <div className="grid lg:grid-cols-3 gap-6 mb-6">
        <Card className="lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              Cartera vs {bench.symbol || benchmark} (base 100)
              <span className="flex items-center gap-4 text-xs font-normal text-muted-foreground">
                <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm" style={{ background: COLOR_PORTFOLIO }} />Cartera</span>
                <span className="flex items-center gap-1.5"><span className="h-2.5 w-2.5 rounded-sm" style={{ background: COLOR_BENCHMARK }} />{bench.symbol || benchmark}</span>
              </span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            {bench.series && bench.series.length > 1 ? (
              <>
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={bench.series}>
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={false} minTickGap={40} />
                    <YAxis tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={false} width={44} domain={["auto", "auto"]} />
                    <Tooltip contentStyle={tooltipStyle} formatter={(v, name) => [fmtNum(v), name === "portfolio" ? "Cartera" : bench.symbol]} />
                    <Line type="monotone" dataKey="portfolio" stroke={COLOR_PORTFOLIO} strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                    <Line type="monotone" dataKey="benchmark" stroke={COLOR_BENCHMARK} strokeWidth={2} dot={false} activeDot={{ r: 4 }} />
                  </LineChart>
                </ResponsiveContainer>
                <div className="flex gap-6 mt-3 text-sm">
                  <span>Cartera: <b className={cn("num", pnlColor(bench.portfolio_cumulative_pct))}>{fmtPct(bench.portfolio_cumulative_pct)}</b></span>
                  <span>{bench.symbol}: <b className={cn("num", pnlColor(bench.benchmark_cumulative_pct))}>{fmtPct(bench.benchmark_cumulative_pct)}</b></span>
                </div>
              </>
            ) : (
              <Empty title="Sin serie comparable todavía"
                hint="Necesita snapshots diarios de la cartera y datos del índice. Se rellenará solo con el backend arrancado." />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Concentración</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm">
            {!concentration.positions ? <Empty title="Sin posiciones" /> : (
              <>
                <MetricRow label="Posiciones" value={concentration.positions} />
                <MetricRow label="Mayor posición" value={concentration.top_holding}
                  sub={concentration.top_weight_pct !== undefined ? `${fmtNum(concentration.top_weight_pct, 1)}%` : null} />
                <MetricRow label="Peso top 5" value={concentration.top5_weight_pct !== undefined ? `${fmtNum(concentration.top5_weight_pct, 1)}%` : "—"} />
                <MetricRow label="Posiciones efectivas" value={concentration.effective_positions ?? "—"}
                  hint="1/HHI: cuántas posiciones equivalentes tienes tras ponderar por tamaño." />
                <div className="pt-3 border-t border-border/60">
                  <div className="text-xs uppercase tracking-wide text-muted-foreground mb-2">Exposición por divisa</div>
                  {by_currency.map((c) => (
                    <div key={c.label} className="flex items-center justify-between py-1">
                      <span>{c.label}</span>
                      <span className="num text-muted-foreground">{fmtMoney(c.value)} · {fmtNum(c.weight_pct, 1)}%</span>
                    </div>
                  ))}
                </div>
              </>
            )}
          </CardContent>
        </Card>
      </div>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Drawdown</CardTitle></CardHeader>
          <CardContent>
            {hasReturns && returns.drawdown_series?.length > 1 ? (
              <ResponsiveContainer width="100%" height={220}>
                <AreaChart data={returns.drawdown_series}>
                  <defs>
                    <linearGradient id="dd" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={COLOR_DRAWDOWN} stopOpacity={0} />
                      <stop offset="95%" stopColor={COLOR_DRAWDOWN} stopOpacity={0.35} />
                    </linearGradient>
                  </defs>
                  <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={false} minTickGap={40} />
                  <YAxis tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={false} width={44}
                    tickFormatter={(v) => `${v}%`} />
                  <Tooltip contentStyle={tooltipStyle} formatter={(v) => [`${fmtNum(v)}%`, "Caída desde máximo"]} />
                  <Area type="monotone" dataKey="dd_pct" stroke={COLOR_DRAWDOWN} strokeWidth={2} fill="url(#dd)" />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <Empty title="Sin histórico de drawdown" hint="Aparecerá cuando haya varios días de snapshots." />
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Ingresos y flujos</CardTitle></CardHeader>
          <CardContent>
            {!income.transactions ? (
              <Empty title="Sin transacciones" hint="Importa el histórico de movimientos de MyInvestor para ver dividendos, compras y comisiones." />
            ) : (
              <>
                <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
                  <MetricRow label="Dividendos cobrados" value={fmtMoney(income.dividends_total)} />
                  <MetricRow label="Comisiones pagadas" value={fmtMoney(income.fees_total)} />
                  <MetricRow label="Total comprado" value={fmtMoney(income.buys_total)} />
                  <MetricRow label="Total vendido" value={fmtMoney(income.sells_total)} />
                </div>
                {income.by_year?.length > 0 && (
                  <Table>
                    <THead>
                      <TR className="hover:bg-transparent">
                        <TH>Año</TH><TH className="text-right">Compras</TH><TH className="text-right">Ventas</TH>
                        <TH className="text-right">Dividendos</TH><TH className="text-right">Comisiones</TH>
                      </TR>
                    </THead>
                    <tbody>
                      {income.by_year.map((y) => (
                        <TR key={y.year}>
                          <TD className="font-medium">{y.year}</TD>
                          <TD className="text-right num text-muted-foreground">{fmtMoney(y.buys)}</TD>
                          <TD className="text-right num text-muted-foreground">{fmtMoney(y.sells)}</TD>
                          <TD className="text-right num">{fmtMoney(y.dividends)}</TD>
                          <TD className="text-right num text-muted-foreground">{fmtMoney(y.fees)}</TD>
                        </TR>
                      ))}
                    </tbody>
                  </Table>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>
    </>
  );
}

function MetricRow({ label, value, sub, hint }) {
  return (
    <div>
      <div className="flex items-center justify-between">
        <span className="text-muted-foreground">{label}</span>
        <span className="font-medium num">{value}{sub && <span className="text-muted-foreground font-normal"> · {sub}</span>}</span>
      </div>
      {hint && <p className="text-xs text-muted-foreground mt-0.5">{hint}</p>}
    </div>
  );
}
