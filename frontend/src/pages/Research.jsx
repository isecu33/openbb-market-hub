import { useState } from "react";
import { api } from "@/lib/api";
import { startJob, useJob } from "@/lib/jobs";
import { cn, fmtNum } from "@/lib/utils";
import { PageHeader } from "@/components/shared";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Table, THead, TR, TH, TD } from "@/components/ui/table";
import { Spinner, ErrorState, Empty } from "@/components/ui/misc";
import { AlertTriangle, FlaskConical, Landmark, RefreshCw } from "lucide-react";

export default function Research() {
  const [tab, setTab] = useState("thesis");
  return (
    <>
      <PageHeader title="Research" subtitle="Tesis temática (de hipótesis macro a candidatas) y seguimiento de operaciones de políticos de EE. UU." />
      <div className="flex gap-2 mb-5">
        <TabBtn active={tab === "thesis"} onClick={() => setTab("thesis")}><FlaskConical className="h-4 w-4" />Tesis temática</TabBtn>
        <TabBtn active={tab === "politicians"} onClick={() => setTab("politicians")}><Landmark className="h-4 w-4" />Políticos (US)</TabBtn>
      </div>
      {tab === "thesis" ? <Thesis /> : <Politicians />}
    </>
  );
}

function TabBtn({ active, children, ...props }) {
  return <button className={cn("px-4 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-2", active ? "bg-primary/15 text-primary" : "text-muted-foreground hover:bg-secondary")} {...props}>{children}</button>;
}

function JobRunning({ elapsed, label }) {
  return (
    <Card><CardContent className="py-12 text-center">
      <div className="flex items-center justify-center gap-3 text-muted-foreground">
        <Spinner className="h-5 w-5" />
        <span className="text-sm">{label} {elapsed > 0 && <span className="num">({fmtNum(elapsed, 0)}s)</span>}</span>
      </div>
      <p className="text-xs text-muted-foreground mt-3">
        El trabajo corre en el servidor: puedes navegar por el resto de la app y volver — no se reiniciará.
      </p>
    </CardContent></Card>
  );
}

function paramFrom(params, key) {
  if (!params) return "";
  return new URLSearchParams(params.replace(/^\?/, "")).get(key) || "";
}

function Thesis() {
  const job = useJob("thesis");
  const [sector, setSector] = useState(() => paramFrom(job.params, "sector"));

  const run = (refresh = false) => {
    const qs = new URLSearchParams();
    if (sector) qs.set("sector", sector);
    if (refresh) qs.set("refresh", "true");
    const q = qs.toString();
    startJob("thesis", api.thesis, q ? `?${q}` : "");
  };

  const data = job.data?.candidates;

  return (
    <>
      <Card className="mb-6"><CardContent className="flex gap-2 pt-5">
        <Input value={sector} onChange={(e) => setSector(e.target.value)} placeholder="Sector (opcional): Utilities, Technology..." />
        <Button onClick={() => run(false)} disabled={job.status === "running"}>Generar candidatas</Button>
        {job.status === "done" && (
          <Button variant="outline" onClick={() => run(true)} title="Ignora la caché y recalcula">
            <RefreshCw className="h-4 w-4" />Recalcular
          </Button>
        )}
      </CardContent></Card>
      {job.status === "running" ? <JobRunning elapsed={job.elapsed} label="Cribando universo..." /> :
        job.status === "error" ? <ErrorState message={job.error} /> :
        !data ? <Card><CardContent><Empty title="Define tu tesis" hint="Lanza el screener para obtener una lista corta de candidatas." /></CardContent></Card> :
        data.length === 0 ? <Card><CardContent><Empty title="Sin candidatas" hint="Prueba a relajar los criterios." /></CardContent></Card> : (
          <Card><CardContent><Table>
            <THead><TR className="hover:bg-transparent"><TH>Símbolo</TH><TH>Nombre</TH><TH className="text-right">Datos</TH></TR></THead>
            <tbody>{data.map((c, i) => (
              <TR key={i}><TD className="font-medium">{c.symbol || c.ticker}</TD><TD>{c.name || "—"}</TD>
                <TD className="text-right text-xs text-muted-foreground num">{Object.entries(c).filter(([k]) => !["symbol", "name", "ticker"].includes(k)).slice(0, 3).map(([k, v]) => `${k}: ${v}`).join("  ·  ") || "—"}</TD></TR>
            ))}</tbody>
          </Table></CardContent></Card>
        )}
    </>
  );
}

function Politicians() {
  const job = useJob("politicians");
  const [name, setName] = useState(() => paramFrom(job.params, "politician"));

  const run = (refresh = false) => {
    const qs = new URLSearchParams();
    if (name) qs.set("politician", name);
    if (refresh) qs.set("refresh", "true");
    const q = qs.toString();
    startJob("politicians", api.politicians, q ? `?${q}` : "");
  };

  const data = job.data?.trades;
  const disclaimer = job.data?.disclaimer;

  return (
    <>
      <div className="rounded-xl border border-yellow-500/30 bg-yellow-500/10 p-3.5 mb-5 flex gap-2.5 text-sm text-yellow-200/90">
        <AlertTriangle className="h-5 w-5 shrink-0 text-yellow-400" />
        <span>{disclaimer || "La STOCK Act permite hasta 45 días de retraso entre la operación y su divulgación. Estos datos son históricos/contextuales, nunca señales en tiempo real."}</span>
      </div>
      <Card className="mb-6"><CardContent className="flex gap-2 pt-5">
        <Input value={name} onChange={(e) => setName(e.target.value)} placeholder="Político (opcional): Nancy Pelosi..." />
        <Button onClick={() => run(false)} disabled={job.status === "running"}>Consultar operaciones</Button>
        {job.status === "done" && (
          <Button variant="outline" onClick={() => run(true)} title="Ignora la caché y recalcula">
            <RefreshCw className="h-4 w-4" />Recalcular
          </Button>
        )}
      </CardContent></Card>
      {job.status === "running" ? <JobRunning elapsed={job.elapsed} label="Consultando Government Trades..." /> :
        job.status === "error" ? <ErrorState message={job.error} /> :
        !data ? <Card><CardContent><Empty title="Consulta Government Trades" hint="Senado + Cámara de Representantes de EE. UU. (proveedor FMP)." /></CardContent></Card> :
        data.length === 0 ? <Card><CardContent><Empty title="Sin operaciones" /></CardContent></Card> : (
          <Card><CardContent><Table>
            <THead><TR className="hover:bg-transparent"><TH>Fecha</TH><TH>Político</TH><TH>Símbolo</TH><TH>Tipo</TH><TH className="text-right">Importe</TH></TR></THead>
            <tbody>{data.slice(0, 100).map((t, i) => (
              <TR key={i}>
                <TD className="num text-muted-foreground">{(t.transaction_date || t.date || "").toString().slice(0, 10)}</TD>
                <TD>{t.representative || t.name || "—"}</TD>
                <TD className="font-medium">{t.symbol || t.ticker || "—"}</TD>
                <TD><Badge tone={/sale|sell/i.test(t.transaction_type || t.type || "") ? "loss" : "gain"}>{t.transaction_type || t.type || "—"}</Badge></TD>
                <TD className="text-right num text-muted-foreground">{t.amount || t.range || "—"}</TD>
              </TR>
            ))}</tbody>
          </Table></CardContent></Card>
        )}
    </>
  );
}
