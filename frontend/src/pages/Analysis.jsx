import { useState, useEffect } from "react";
import { useSearchParams } from "react-router-dom";
import { api } from "@/lib/api";
import { fmtNum, fmtPct, fmtMoney, pnlColor, cn } from "@/lib/utils";
import { PageHeader, SentimentBadge } from "@/components/shared";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loading, ErrorState, Empty } from "@/components/ui/misc";
import { Search } from "lucide-react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer } from "recharts";

const RANGES = [{ d: 30, l: "1M" }, { d: 90, l: "3M" }, { d: 180, l: "6M" }, { d: 365, l: "1A" }, { d: 1825, l: "5A" }];

export default function Analysis() {
  const [params, setParams] = useSearchParams();
  const [symbol, setSymbol] = useState(params.get("symbol") || "");
  const [active, setActive] = useState(params.get("symbol") || "");
  const [days, setDays] = useState(180);
  const [quote, setQuote] = useState(null);
  const [series, setSeries] = useState(null);
  const [news, setNews] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const run = async (sym) => {
    if (!sym) return;
    setLoading(true); setError(null); setActive(sym); setParams({ symbol: sym });
    try {
      const [q, h, n] = await Promise.all([
        api.quote(sym), api.marketHistory(sym, days), api.newsSymbol(sym),
      ]);
      setQuote(q); setSeries(h.series); setNews(n.news);
    } catch (e) { setError(e.message); } finally { setLoading(false); }
  };

  useEffect(() => { if (active) api.marketHistory(active, days).then((h) => setSeries(h.series)); /* eslint-disable-next-line */ }, [days]);
  useEffect(() => { if (params.get("symbol")) run(params.get("symbol")); /* eslint-disable-next-line */ }, []);

  return (
    <>
      <PageHeader title="Análisis" subtitle="Cotización, evolución histórica y noticias de cualquier acción o ETF cotizado." />
      <Card className="mb-6"><CardContent className="flex gap-2 pt-5">
        <Input value={symbol} onChange={(e) => setSymbol(e.target.value.toUpperCase())} placeholder="Símbolo (AAPL, MSFT, NVDA...)" onKeyDown={(e) => e.key === "Enter" && run(symbol)} />
        <Button onClick={() => run(symbol)}><Search className="h-4 w-4" />Analizar</Button>
      </CardContent></Card>

      {loading ? <Loading /> : error ? <ErrorState message={error} /> : !active ? (
        <Card><CardContent><Empty title="Busca un símbolo" hint="Escribe un ticker para ver su gráfico, cotización y noticias." /></CardContent></Card>
      ) : (
        <>
          {quote && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
              <Stat label={active} value={quote.price ? fmtNum(quote.price) : "—"} sub={quote.name} />
              <Stat label="Variación día" value={quote.change_pct != null ? fmtPct(quote.change_pct) : "—"} color={pnlColor(quote.change_pct)} />
              <Stat label="Máx / Mín día" value={quote.day_high ? `${fmtNum(quote.day_high)} / ${fmtNum(quote.day_low)}` : "—"} />
              <Stat label="Volumen" value={quote.volume ? fmtNum(quote.volume, 0) : "—"} />
            </div>
          )}

          <Card className="mb-6">
            <CardHeader className="flex-row items-center justify-between">
              <CardTitle>Precio histórico</CardTitle>
              <div className="flex gap-1">
                {RANGES.map((r) => (
                  <button key={r.d} onClick={() => setDays(r.d)} className={cn("px-2.5 py-1 rounded-md text-xs font-medium", days === r.d ? "bg-primary/20 text-primary" : "text-muted-foreground hover:bg-secondary")}>{r.l}</button>
                ))}
              </div>
            </CardHeader>
            <CardContent>
              {series && series.length > 1 ? (
                <ResponsiveContainer width="100%" height={320}>
                  <AreaChart data={series}>
                    <defs><linearGradient id="ga" x1="0" y1="0" x2="0" y2="1"><stop offset="5%" stopColor="#3b82f6" stopOpacity={0.4} /><stop offset="95%" stopColor="#3b82f6" stopOpacity={0} /></linearGradient></defs>
                    <XAxis dataKey="date" tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={false} minTickGap={50} />
                    <YAxis domain={["auto", "auto"]} tick={{ fontSize: 11, fill: "#64748b" }} tickLine={false} axisLine={false} width={50} />
                    <Tooltip contentStyle={{ background: "#0b1220", border: "1px solid #1e293b", borderRadius: 10 }} formatter={(v) => fmtNum(v)} />
                    <Area type="monotone" dataKey="close" stroke="#3b82f6" strokeWidth={2} fill="url(#ga)" />
                  </AreaChart>
                </ResponsiveContainer>
              ) : <Empty title="Sin datos de precio" hint="El proveedor no devolvió histórico para este símbolo." />}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Noticias de {active}</CardTitle></CardHeader>
            <CardContent className="space-y-3">
              {!news?.length ? <Empty title="Sin noticias" /> : news.map((n, i) => (
                <div key={i} className="flex items-start justify-between gap-3 py-1.5 border-b border-border/40 last:border-0">
                  <a href={n.url} target="_blank" rel="noreferrer" className="text-sm hover:text-primary">{n.title}<div className="text-xs text-muted-foreground mt-0.5">{n.source} · {n.date}</div></a>
                  <SentimentBadge sentiment={n.sentiment} />
                </div>
              ))}
            </CardContent>
          </Card>
        </>
      )}
    </>
  );
}

function Stat({ label, value, sub, color }) {
  return (
    <div className="glass rounded-xl p-4">
      <div className="text-xs uppercase text-muted-foreground truncate">{label}</div>
      <div className={cn("text-xl font-bold num mt-1", color)}>{value}</div>
      {sub && <div className="text-xs text-muted-foreground truncate">{sub}</div>}
    </div>
  );
}
