import { useState } from "react";
import { api } from "@/lib/api";
import { fmtMoney, fmtNum } from "@/lib/utils";
import { PageHeader } from "@/components/shared";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Table, THead, TR, TH, TD } from "@/components/ui/table";
import { ErrorState, Empty } from "@/components/ui/misc";
import { UploadCloud, FileSpreadsheet, CheckCircle2 } from "lucide-react";

export default function Import() {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [result, setResult] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const onFile = async (f) => {
    if (!f) return;
    setFile(f); setPreview(null); setResult(null); setError(null); setBusy(true);
    try { const p = await api.importPreview(f); if (p.detail) throw new Error(p.detail); setPreview(p); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  };

  const commit = async () => {
    setBusy(true); setError(null);
    try { const r = await api.importCommit(file); if (r.detail) throw new Error(r.detail); setResult(r); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  };

  return (
    <>
      <PageHeader title="Importar de MyInvestor" subtitle="Sube tu export de cartera o de movimientos (CSV o Excel). Detecta automáticamente fondos (por ISIN), acciones/ETF y transacciones, soportando el formato numérico europeo." />

      <Card className="mb-6">
        <CardContent className="pt-6">
          <label className="border-2 border-dashed border-border rounded-xl p-10 flex flex-col items-center justify-center gap-3 cursor-pointer hover:border-primary/50 hover:bg-secondary/20 transition-colors">
            <div className="h-14 w-14 rounded-full bg-primary/15 flex items-center justify-center"><UploadCloud className="h-7 w-7 text-primary" /></div>
            <div className="text-center">
              <div className="font-medium">{file ? file.name : "Arrastra o haz clic para subir tu archivo"}</div>
              <div className="text-sm text-muted-foreground">CSV, XLSX o XLS exportado de MyInvestor</div>
            </div>
            <input type="file" accept=".csv,.xlsx,.xls,.xlsm" className="hidden" onChange={(e) => onFile(e.target.files[0])} />
          </label>
          {busy && !preview && <p className="text-sm text-muted-foreground mt-3 text-center">Analizando archivo...</p>}
          {error && <div className="mt-4"><ErrorState message={error} /></div>}
        </CardContent>
      </Card>

      {result && (
        <Card className="mb-6 border-[hsl(var(--gain)/0.4)]">
          <CardContent className="pt-6 flex items-center gap-3">
            <CheckCircle2 className="h-6 w-6 text-[hsl(var(--gain))]" />
            <div>
              <div className="font-medium">Importación completada ({result.kind === "transactions" ? "movimientos" : "posiciones"})</div>
              <div className="text-sm text-muted-foreground num">{JSON.stringify(result.result)}</div>
              {result.warnings?.length > 0 && <div className="text-sm text-yellow-400 mt-1">{result.warnings.join(" ")}</div>}
            </div>
          </CardContent>
        </Card>
      )}

      {preview && !result && (
        <Card>
          <CardHeader className="flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2"><FileSpreadsheet className="h-4 w-4" />Vista previa · {preview.kind === "transactions" ? "Movimientos" : "Posiciones"}</CardTitle>
            <Button onClick={commit} disabled={busy}>{busy ? "Importando..." : "Confirmar e importar"}</Button>
          </CardHeader>
          <CardContent>
            {preview.warnings?.length > 0 && <div className="mb-3 text-sm text-yellow-400">{preview.warnings.join(" ")}</div>}
            <div className="text-xs text-muted-foreground mb-3">Columnas detectadas: {Object.entries(preview.detected_columns || {}).map(([k, v]) => `${k}→${v}`).join(", ") || "ninguna"}</div>
            {preview.kind === "positions" ? (
              preview.positions.length === 0 ? <Empty title="No se detectaron posiciones" /> :
              <Table>
                <THead><TR className="hover:bg-transparent"><TH>Nombre</TH><TH>ISIN/Ticker</TH><TH>Tipo</TH><TH className="text-right">Cant.</TH><TH className="text-right">Invertido</TH><TH className="text-right">Valor</TH></TR></THead>
                <tbody>{preview.positions.map((p, i) => (
                  <TR key={i}><TD className="font-medium">{p.name}</TD><TD className="num text-muted-foreground">{p.isin || p.symbol}</TD>
                    <TD><Badge tone="neutral">{p.kind}</Badge></TD><TD className="text-right num">{fmtNum(p.quantity, 4)}</TD>
                    <TD className="text-right num">{p.invested != null ? fmtMoney(p.invested, p.currency) : "—"}</TD>
                    <TD className="text-right num">{p.market_value != null ? fmtMoney(p.market_value, p.currency) : "—"}</TD></TR>
                ))}</tbody>
              </Table>
            ) : (
              <Table>
                <THead><TR className="hover:bg-transparent"><TH>Fecha</TH><TH>Tipo</TH><TH>Producto</TH><TH className="text-right">Cant.</TH><TH className="text-right">Importe</TH></TR></THead>
                <tbody>{preview.transactions.map((t, i) => (
                  <TR key={i}><TD className="num text-muted-foreground">{t.date}</TD><TD><Badge tone={t.tx_type === "sell" ? "loss" : "gain"}>{t.tx_type}</Badge></TD>
                    <TD>{t.name}</TD><TD className="text-right num">{fmtNum(t.quantity, 4)}</TD><TD className="text-right num">{t.amount != null ? fmtMoney(t.amount, "EUR") : "—"}</TD></TR>
                ))}</tbody>
              </Table>
            )}
          </CardContent>
        </Card>
      )}
    </>
  );
}
