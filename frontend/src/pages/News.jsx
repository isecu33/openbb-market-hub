import { useState } from "react";
import { useApi } from "@/hooks/useApi";
import { api } from "@/lib/api";
import { cn } from "@/lib/utils";
import { PageHeader, SentimentBadge } from "@/components/shared";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Loading, ErrorState, Empty } from "@/components/ui/misc";
import { ExternalLink, Newspaper, RefreshCw, Flame } from "lucide-react";

const CATEGORY_LABEL = {
  "m&a": "M&A", resultados: "Resultados", "regulación": "Regulación",
  "dirección": "Dirección", analistas: "Analistas", capital: "Capital", macro: "Macro",
};

export default function News() {
  const [onlyImportant, setOnlyImportant] = useState(false);
  const feed = useApi(() => api.newsFeed(onlyImportant ? 40 : 0), [onlyImportant]);
  const [refreshing, setRefreshing] = useState(false);

  const refresh = async () => {
    setRefreshing(true);
    try { await api.newsRefresh(); feed.reload(); } finally { setRefreshing(false); }
  };

  const summary = feed.data?.sentiment_summary;

  return (
    <>
      <PageHeader title="Noticias"
        subtitle="Feed persistente de tus activos y del mercado global, con sentimiento e importancia. El backend lo actualiza solo cada hora.">
        <Button variant="outline" size="sm" onClick={refresh} disabled={refreshing}>
          <RefreshCw className={cn("h-4 w-4", refreshing && "animate-spin")} />
          {refreshing ? "Descargando..." : "Actualizar ahora"}
        </Button>
      </PageHeader>

      <div className="flex flex-wrap items-center gap-3 mb-5">
        <button onClick={() => setOnlyImportant(false)}
          className={cn("px-4 py-1.5 rounded-lg text-sm font-medium transition-colors", !onlyImportant ? "bg-primary/15 text-primary" : "text-muted-foreground hover:bg-secondary")}>
          Todas
        </button>
        <button onClick={() => setOnlyImportant(true)}
          className={cn("px-4 py-1.5 rounded-lg text-sm font-medium transition-colors flex items-center gap-1.5", onlyImportant ? "bg-primary/15 text-primary" : "text-muted-foreground hover:bg-secondary")}>
          <Flame className="h-4 w-4" /> Solo importantes
        </button>
        {summary && (
          <div className="flex gap-2 ml-auto">
            <Badge tone="gain">{summary.positive} positivas</Badge>
            <Badge tone="neutral">{summary.neutral} neutras</Badge>
            <Badge tone="loss">{summary.negative} negativas</Badge>
          </div>
        )}
      </div>

      {feed.loading ? <Loading label="Cargando feed..." /> : feed.error ? <ErrorState message={feed.error} /> :
        !feed.data?.news?.length ? (
          <Card><CardContent>
            <Empty title="Sin noticias almacenadas"
              hint="Pulsa 'Actualizar ahora' para descargar el primer lote, o añade activos con ticker a tu cartera/watchlist." />
          </CardContent></Card>
        ) : (
          <div className="space-y-3">
            {feed.data.news.map((n) => (
              <Card key={n.id} className={cn("hover:border-primary/40 transition-colors",
                n.importance >= 40 && "border-yellow-500/30")}>
                <CardContent className="pt-5 flex gap-4">
                  <div className="h-10 w-10 rounded-lg bg-secondary flex items-center justify-center shrink-0">
                    {n.importance >= 40
                      ? <Flame className="h-5 w-5 text-yellow-400" />
                      : <Newspaper className="h-5 w-5 text-muted-foreground" />}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-start justify-between gap-3">
                      <a href={n.url} target="_blank" rel="noreferrer" className="font-medium hover:text-primary flex items-start gap-1.5">
                        {n.title} {n.url && <ExternalLink className="h-3.5 w-3.5 shrink-0 mt-1 opacity-60" />}
                      </a>
                      <div className="flex items-center gap-2 shrink-0">
                        {n.category && <Badge tone="primary">{CATEGORY_LABEL[n.category] || n.category}</Badge>}
                        <SentimentBadge sentiment={n.sentiment} />
                      </div>
                    </div>
                    {n.summary && <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{n.summary}</p>}
                    <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                      {n.symbol && <Badge tone="neutral">{n.symbol}</Badge>}
                      <span>{n.source}</span><span>·</span><span>{n.date}</span>
                      {n.importance > 0 && <><span>·</span><span>relevancia {n.importance}/100</span></>}
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
    </>
  );
}
