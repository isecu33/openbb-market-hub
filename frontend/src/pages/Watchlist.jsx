import { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { fmtNum } from "@/lib/utils";
import { PageHeader } from "@/components/shared";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Loading, ErrorState, Empty } from "@/components/ui/misc";
import { Star, Trash2, Plus } from "lucide-react";
import { Link } from "react-router-dom";

export default function Watchlist() {
  const wl = useApi(() => api.watchlist(), []);
  const [sym, setSym] = useState("");
  const [busy, setBusy] = useState(false);

  const add = async () => {
    if (!sym.trim()) return;
    setBusy(true);
    try { await api.addWatch({ symbol: sym.trim().toUpperCase(), kind: "equity" }); setSym(""); wl.reload(); }
    finally { setBusy(false); }
  };
  const remove = async (id) => { await api.removeWatch(id); wl.reload(); };

  return (
    <>
      <PageHeader title="Watchlist" subtitle="Activos que sigues sin tenerlos necesariamente en cartera." />
      <Card className="mb-6"><CardContent className="flex gap-2 pt-5">
        <Input value={sym} onChange={(e) => setSym(e.target.value)} placeholder="Añadir ticker (p. ej. NVDA)" onKeyDown={(e) => e.key === "Enter" && add()} />
        <Button onClick={add} disabled={busy}><Plus className="h-4 w-4" />Añadir</Button>
      </CardContent></Card>

      {wl.loading ? <Loading /> : wl.error ? <ErrorState message={wl.error} /> :
        wl.data.length === 0 ? <Card><CardContent><Empty title="Watchlist vacía" hint="Añade tickers para seguir su precio y noticias." /></CardContent></Card> : (
          <div className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
            {wl.data.map((a) => (
              <Card key={a.asset_id}><CardContent className="pt-5 flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-lg bg-primary/15 flex items-center justify-center"><Star className="h-5 w-5 text-primary" /></div>
                  <div>
                    <Link to={`/analisis?symbol=${a.symbol}`} className="font-semibold hover:text-primary">{a.symbol || a.name}</Link>
                    <div className="text-xs text-muted-foreground">{a.last_price ? fmtNum(a.last_price) : "Sin precio"}</div>
                  </div>
                </div>
                <Button variant="ghost" size="icon" onClick={() => remove(a.asset_id)}><Trash2 className="h-4 w-4 text-muted-foreground" /></Button>
              </CardContent></Card>
            ))}
          </div>
        )}
    </>
  );
}
