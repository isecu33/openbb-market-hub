import { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Loading, ErrorState, Empty } from "@/components/ui/misc";
import { Bell, Trash2, Plus, CheckCheck, Play } from "lucide-react";

const KINDS = [
  { v: "price_above", l: "Precio por encima de" },
  { v: "price_below", l: "Precio por debajo de" },
  { v: "pct_change_day", l: "Variación diaria supera (%)" },
  { v: "pct_from_cost", l: "P&L de la posición cruza (%)" },
  { v: "news", l: "Noticia relevante (sentimiento)" },
  { v: "politician", l: "Trade de político en el ticker" },
];
const kindLabel = (v) => KINDS.find((k) => k.v === v)?.l || v;

export default function Alerts() {
  const alerts = useApi(() => api.alerts(), []);
  const events = useApi(() => api.alertEvents(false), []);
  const [f, setF] = useState({ symbol: "", kind: "price_above", threshold: "", note: "" });
  const [busy, setBusy] = useState(false);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const create = async () => {
    setBusy(true);
    try {
      await api.createAlert({ symbol: f.symbol.toUpperCase() || null, kind: f.kind, threshold: f.threshold ? parseFloat(f.threshold) : null, note: f.note || null });
      setF({ symbol: "", kind: "price_above", threshold: "", note: "" }); alerts.reload();
    } finally { setBusy(false); }
  };
  const del = async (id) => { await api.deleteAlert(id); alerts.reload(); };
  const toggle = async (a) => { await api.updateAlert(a.id, { kind: a.kind, threshold: a.threshold, note: a.note, active: !a.active }); alerts.reload(); };
  const checkNow = async () => { setBusy(true); try { await api.checkAlerts(); events.reload(); } finally { setBusy(false); } };
  const readAll = async () => { await api.markAllRead(); events.reload(); };

  const needsThreshold = !["news", "politician"].includes(f.kind);

  return (
    <>
      <PageHeader title="Alertas" subtitle="Reglas que el backend evalúa periódicamente. Las que se cumplen aparecen abajo como eventos.">
        <Button variant="outline" onClick={checkNow} disabled={busy}><Play className="h-4 w-4" />Comprobar ahora</Button>
      </PageHeader>

      <Card className="mb-6">
        <CardHeader><CardTitle>Nueva alerta</CardTitle></CardHeader>
        <CardContent className="grid md:grid-cols-5 gap-3 items-end">
          <div><label className="text-xs text-muted-foreground">Ticker</label><Input value={f.symbol} onChange={set("symbol")} placeholder="AAPL" /></div>
          <div className="md:col-span-2"><label className="text-xs text-muted-foreground">Condición</label>
            <Select value={f.kind} onChange={set("kind")}>{KINDS.map((k) => <option key={k.v} value={k.v}>{k.l}</option>)}</Select></div>
          <div><label className="text-xs text-muted-foreground">Umbral</label><Input value={f.threshold} onChange={set("threshold")} type="number" disabled={!needsThreshold} placeholder={needsThreshold ? "150" : "n/a"} /></div>
          <Button onClick={create} disabled={busy}><Plus className="h-4 w-4" />Crear</Button>
        </CardContent>
      </Card>

      <div className="grid lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Reglas activas</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {alerts.loading ? <Loading /> : alerts.error ? <ErrorState message={alerts.error} /> :
              alerts.data.length === 0 ? <Empty title="Sin reglas" hint="Crea una alerta arriba." /> :
              alerts.data.map((a) => (
                <div key={a.id} className="flex items-center justify-between py-2 border-b border-border/40 last:border-0">
                  <div>
                    <div className="font-medium text-sm flex items-center gap-2">{a.label || a.symbol || "—"} <Badge tone={a.active ? "primary" : "neutral"}>{a.active ? "activa" : "pausada"}</Badge></div>
                    <div className="text-xs text-muted-foreground">{kindLabel(a.kind)} {a.threshold != null && <span className="num">{a.threshold}</span>} · {a.trigger_count} disparos</div>
                  </div>
                  <div className="flex gap-1">
                    <Button variant="ghost" size="sm" onClick={() => toggle(a)}>{a.active ? "Pausar" : "Activar"}</Button>
                    <Button variant="ghost" size="icon" onClick={() => del(a.id)}><Trash2 className="h-4 w-4 text-muted-foreground" /></Button>
                  </div>
                </div>
              ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle>Eventos disparados</CardTitle>
            <Button variant="ghost" size="sm" onClick={readAll}><CheckCheck className="h-4 w-4" />Marcar leídas</Button>
          </CardHeader>
          <CardContent className="space-y-2">
            {events.loading ? <Loading /> :
              !events.data?.length ? <Empty title="Nada todavía" hint="Cuando una alerta se cumpla aparecerá aquí." /> :
              events.data.map((e) => (
                <div key={e.id} className="flex items-start gap-2 py-2 border-b border-border/40 last:border-0">
                  <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center shrink-0", e.read ? "bg-secondary" : "bg-primary/15")}><Bell className={cn("h-4 w-4", e.read ? "text-muted-foreground" : "text-primary")} /></div>
                  <div className="text-sm"><div>{e.message}</div><div className="text-xs text-muted-foreground">{new Date(e.triggered_at).toLocaleString("es-ES")}</div></div>
                </div>
              ))}
          </CardContent>
        </Card>
      </div>
    </>
  );
}
