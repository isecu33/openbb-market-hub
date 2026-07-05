import { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { startJob, useJob } from "@/lib/jobs";
import { cn, fmtNum, fmtPct, pnlColor } from "@/lib/utils";
import { PageHeader } from "@/components/shared";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, THead, TR, TH, TD } from "@/components/ui/table";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Spinner, Loading, ErrorState, Empty } from "@/components/ui/misc";
import { AlertTriangle, Sparkles, RefreshCw } from "lucide-react";

const TREND_TONE = { alcista: "gain", bajista: "loss", mixta: "neutral" };

export default function Suggestions() {
  const [period, setPeriod] = useState("daily");
  const latest = useApi(() => api.suggestions(period), [period]);
  const job = useJob(`suggestion-${period}`);

  const generate = () => {
    startJob(`suggestion-${period}`, (p) => api.suggestionsGenerate(p), `?period=${period}&refresh=true`);
  };

  // Si el job terminó después de la última carga, su resultado es el más fresco.
  const s = (job.status === "done" && job.data?.suggestion) || (latest.data && !latest.data.empty ? latest.data : null);

  return (
    <>
      <PageHeader title="Sugerencias"
        subtitle="Ranking cuantitativo (tendencia + momentum) del universo seguido y briefing de mercado. Se genera solo: a diario y cada lunes.">
        <div className="flex gap-2">
          <TabBtn active={period === "daily"} onClick={() => setPeriod("daily")}>Diaria</TabBtn>
          <TabBtn active={period === "weekly"} onClick={() => setPeriod("weekly")}>Semanal</TabBtn>
          <Button onClick={generate} disabled={job.status === "running"}>
            <RefreshCw className={cn("h-4 w-4", job.status === "running" && "animate-spin")} />
            Generar ahora
          </Button>
        </div>
      </PageHeader>

      <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-3.5 mb-5 flex gap-2.5 text-sm text-yellow-200/90">
        <AlertTriangle className="h-5 w-5 shrink-0 text-yellow-400" />
        <span>{s?.disclaimer || "Generado automáticamente a partir de señales cuantitativas y noticias. NO es asesoramiento financiero."}</span>
      </div>

      {job.status === "running" && (
        <Card className="mb-5"><CardContent className="py-6 text-center">
          <div className="flex items-center justify-center gap-3 text-muted-foreground text-sm">
            <Spinner className="h-5 w-5" />
            Calculando señales del universo... {job.elapsed > 0 && <span className="num">({fmtNum(job.elapsed, 0)}s)</span>}
          </div>
          <p className="text-xs text-muted-foreground mt-2">Corre en el servidor: puedes navegar y volver.</p>
        </CardContent></Card>
      )}
      {job.status === "error" && <div className="mb-5"><ErrorState message={job.error} /></div>}

      {latest.loading && !s ? <Loading label="Buscando última sugerencia..." /> :
        !s ? (
          <Card><CardContent>
            <Empty title="Aún no hay sugerencias"
              hint="Pulsa 'Generar ahora' (tarda ~1 minuto) o espera a la generación automática del scheduler." />
          </CardContent></Card>
        ) : (
          <>
            <Card className="mb-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Sparkles className="h-4 w-4 text-primary" />
                  Briefing {s.period === "weekly" ? "semanal" : "diario"}
                  <Badge tone={s.engine === "claude" ? "primary" : "neutral"}>
                    {s.engine === "claude" ? "Redactado por Claude" : "Motor de reglas"}
                  </Badge>
                  <span className="ml-auto text-xs font-normal text-muted-foreground">
                    {new Date(s.generated_at + "Z").toLocaleString("es-ES")}
                  </span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm whitespace-pre-line leading-relaxed">{s.briefing}</p>
              </CardContent>
            </Card>

            <div className="grid lg:grid-cols-2 gap-6 mb-6">
              <SignalTable title="Mejores señales" rows={s.top_signals} />
              <SignalTable title="Señales más débiles" rows={s.bottom_signals} />
            </div>

            <Card>
              <CardHeader><CardTitle>Índices y sectores</CardTitle></CardHeader>
              <CardContent>
                <SignalRows rows={s.index_signals} />
              </CardContent>
            </Card>
          </>
        )}
    </>
  );
}

function TabBtn({ active, ...props }) {
  return <button className={cn("px-4 py-1.5 rounded-lg text-sm font-medium transition-colors", active ? "bg-primary/15 text-primary" : "text-muted-foreground hover:bg-secondary")} {...props} />;
}

function SignalTable({ title, rows }) {
  return (
    <Card>
      <CardHeader><CardTitle>{title}</CardTitle></CardHeader>
      <CardContent>
        {!rows?.length ? <Empty title="Sin datos" /> : <SignalRows rows={rows} />}
      </CardContent>
    </Card>
  );
}

function SignalRows({ rows }) {
  return (
    <Table>
      <THead>
        <TR className="hover:bg-transparent">
          <TH>Activo</TH><TH>Tendencia</TH>
          <TH className="text-right">3 meses</TH>
          <TH className="text-right">vs máx. 52s</TH>
          <TH className="text-right">Score</TH>
        </TR>
      </THead>
      <tbody>
        {rows.map((r) => (
          <TR key={r.symbol}>
            <TD>
              <div className="font-medium">{r.symbol}</div>
              <div className="text-xs text-muted-foreground">{r.label !== r.symbol ? r.label : ""}</div>
            </TD>
            <TD><Badge tone={TREND_TONE[r.trend] || "neutral"}>{r.trend}</Badge></TD>
            <TD className={cn("text-right num", pnlColor(r.ret_3m_pct))}>{fmtPct(r.ret_3m_pct)}</TD>
            <TD className="text-right num text-muted-foreground">{fmtPct(r.from_52w_high_pct)}</TD>
            <TD className="text-right num font-semibold">{fmtNum(r.score, 0)}</TD>
          </TR>
        ))}
      </tbody>
    </Table>
  );
}
