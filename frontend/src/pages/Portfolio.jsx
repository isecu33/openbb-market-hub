import { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { fmtMoney, fmtNum, fmtPct, pnlColor, cn } from "@/lib/utils";
import { PageHeader } from "@/components/shared";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Table, THead, TR, TH, TD } from "@/components/ui/table";
import { Button } from "@/components/ui/button";
import { Input, Select } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Loading, ErrorState, Empty } from "@/components/ui/misc";
import { Plus, Trash2, X, Download } from "lucide-react";

const KIND_LABEL = { fund: "Fondo", etf: "ETF", equity: "Acción", crypto: "Cripto", other: "Otro" };

export default function Portfolio() {
  const pf = useApi(() => api.portfolio(), []);
  const [showForm, setShowForm] = useState(false);

  if (pf.loading) return <Loading />;
  if (pf.error) return <ErrorState message={pf.error} />;
  const { holdings, summary } = pf.data;

  const remove = async (id) => { await api.deletePosition(id); pf.reload(); };

  return (
    <>
      <PageHeader title="Cartera" subtitle="Tus posiciones consolidadas con valoración y P&L. Los fondos se valoran con el último valor liquidativo importado; las acciones/ETF con precio en vivo.">
        <a href="/api/portfolio/export/holdings.csv" download>
          <Button variant="outline"><Download className="h-4 w-4" />Exportar CSV</Button>
        </a>
        <Button onClick={() => setShowForm((v) => !v)}>{showForm ? <X className="h-4 w-4" /> : <Plus className="h-4 w-4" />}{showForm ? "Cerrar" : "Añadir posición"}</Button>
      </PageHeader>

      {showForm && <PositionForm onDone={() => { setShowForm(false); pf.reload(); }} />}

      <div className="grid grid-cols-3 gap-4 mb-6">
        <SummaryCell label="Valor total" value={fmtMoney(summary.total_value, summary.base_currency)} />
        <SummaryCell label="Invertido" value={fmtMoney(summary.total_invested, summary.base_currency)} />
        <SummaryCell label="P&L" value={fmtMoney(summary.total_pnl, summary.base_currency)} pct={summary.total_pnl_pct} />
      </div>

      <Card>
        <CardHeader><CardTitle>Posiciones ({holdings.length})</CardTitle></CardHeader>
        <CardContent>
          {holdings.length === 0 ? (
            <Empty title="Cartera vacía" hint="Importa tu archivo de MyInvestor o añade una posición manual." />
          ) : (
            <Table>
              <THead>
                <TR className="hover:bg-transparent">
                  <TH>Activo</TH><TH>Tipo</TH><TH className="text-right">Cant.</TH>
                  <TH className="text-right">P. medio</TH><TH className="text-right">Últ. precio</TH>
                  <TH className="text-right">Invertido</TH><TH className="text-right">Valor</TH>
                  <TH className="text-right">P&L</TH><TH className="text-right">Peso</TH><TH></TH>
                </TR>
              </THead>
              <tbody>
                {holdings.map((h) => (
                  <TR key={h.asset_id}>
                    <TD>
                      <div className="font-medium">{h.symbol || h.name}</div>
                      <div className="text-xs text-muted-foreground">{h.symbol ? h.name : h.isin}</div>
                    </TD>
                    <TD><Badge tone="neutral">{KIND_LABEL[h.kind] || h.kind}</Badge></TD>
                    <TD className="text-right num">{fmtNum(h.quantity, 4)}</TD>
                    <TD className="text-right num text-muted-foreground">{h.avg_price ? fmtNum(h.avg_price) : "—"}</TD>
                    <TD className="text-right num">{h.last_price ? fmtNum(h.last_price) : "—"}<div className="text-[10px] text-muted-foreground">{h.price_source}</div></TD>
                    <TD className="text-right num text-muted-foreground">{fmtMoney(h.invested, h.currency)}</TD>
                    <TD className="text-right num font-medium">{fmtMoney(h.market_value, h.currency)}</TD>
                    <TD className={cn("text-right num font-medium", pnlColor(h.pnl))}>
                      {fmtMoney(h.pnl, h.currency)}<div className="text-xs">{fmtPct(h.pnl_pct)}</div>
                    </TD>
                    <TD className="text-right num text-muted-foreground">{fmtNum(h.weight, 1)}%</TD>
                    <TD><Button variant="ghost" size="icon" onClick={() => remove(h.asset_id)}><Trash2 className="h-4 w-4 text-muted-foreground" /></Button></TD>
                  </TR>
                ))}
              </tbody>
            </Table>
          )}
        </CardContent>
      </Card>
    </>
  );
}

function SummaryCell({ label, value, pct }) {
  return (
    <div className="glass rounded-xl p-4">
      <div className="text-xs uppercase text-muted-foreground">{label}</div>
      <div className="text-xl font-bold num mt-1">{value}</div>
      {pct !== undefined && <div className={cn("text-sm num", pnlColor(pct))}>{fmtPct(pct)}</div>}
    </div>
  );
}

function PositionForm({ onDone }) {
  const [f, setF] = useState({ kind: "fund", name: "", symbol: "", isin: "", quantity: "", avg_price: "", invested_amount: "", currency: "EUR" });
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState(null);
  const set = (k) => (e) => setF({ ...f, [k]: e.target.value });

  const submit = async () => {
    setBusy(true); setErr(null);
    try {
      await api.upsertPosition({
        ...f,
        quantity: parseFloat(f.quantity) || 0,
        avg_price: f.avg_price ? parseFloat(f.avg_price) : null,
        invested_amount: f.invested_amount ? parseFloat(f.invested_amount) : null,
      });
      onDone();
    } catch (e) { setErr(e.message); } finally { setBusy(false); }
  };

  return (
    <Card className="mb-6">
      <CardHeader><CardTitle>Nueva posición</CardTitle></CardHeader>
      <CardContent>
        {err && <div className="mb-3"><ErrorState message={err} /></div>}
        <div className="grid md:grid-cols-4 gap-3">
          <div><label className="text-xs text-muted-foreground">Tipo</label>
            <Select value={f.kind} onChange={set("kind")}>
              <option value="fund">Fondo</option><option value="etf">ETF</option>
              <option value="equity">Acción</option><option value="crypto">Cripto</option><option value="other">Otro</option>
            </Select></div>
          <div><label className="text-xs text-muted-foreground">Nombre</label><Input value={f.name} onChange={set("name")} placeholder="Fundsmith Equity" /></div>
          <div><label className="text-xs text-muted-foreground">Ticker (acciones/ETF)</label><Input value={f.symbol} onChange={set("symbol")} placeholder="AAPL" /></div>
          <div><label className="text-xs text-muted-foreground">ISIN (fondos)</label><Input value={f.isin} onChange={set("isin")} placeholder="LU0690375182" /></div>
          <div><label className="text-xs text-muted-foreground">Participaciones / Cantidad</label><Input value={f.quantity} onChange={set("quantity")} type="number" /></div>
          <div><label className="text-xs text-muted-foreground">Precio medio</label><Input value={f.avg_price} onChange={set("avg_price")} type="number" /></div>
          <div><label className="text-xs text-muted-foreground">Importe invertido</label><Input value={f.invested_amount} onChange={set("invested_amount")} type="number" /></div>
          <div><label className="text-xs text-muted-foreground">Divisa</label><Input value={f.currency} onChange={set("currency")} /></div>
        </div>
        <div className="flex justify-end mt-4"><Button onClick={submit} disabled={busy}>{busy ? "Guardando..." : "Guardar posición"}</Button></div>
      </CardContent>
    </Card>
  );
}
