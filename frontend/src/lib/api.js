// Cliente API. Base relativa: en dev Vite proxya /api -> :8000; en prod
// el backend FastAPI sirve el build y responde /api en el mismo origen.
const BASE = "/api";

async function req(path, options = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...options,
  });
  if (!res.ok) {
    let detail = res.statusText;
    try { detail = (await res.json()).detail || detail; } catch {}
    throw new Error(detail);
  }
  return res.json();
}

export const api = {
  status: () => req("/status"),

  // Portfolio
  portfolio: () => req("/portfolio"),
  history: (days = 365) => req(`/portfolio/history?days=${days}`),
  metrics: (days = 365, benchmark = "SPY") =>
    req(`/portfolio/metrics?days=${days}&benchmark=${encodeURIComponent(benchmark)}`),
  transactions: () => req("/portfolio/transactions"),
  upsertPosition: (body) => req("/portfolio/positions", { method: "POST", body: JSON.stringify(body) }),
  deletePosition: (assetId) => req(`/portfolio/positions/${assetId}`, { method: "DELETE" }),

  // Import (multipart)
  importPreview: (file) => {
    const fd = new FormData(); fd.append("file", file);
    return fetch(`${BASE}/portfolio/import/preview`, { method: "POST", body: fd }).then(r => r.json());
  },
  importCommit: (file) => {
    const fd = new FormData(); fd.append("file", file);
    return fetch(`${BASE}/portfolio/import`, { method: "POST", body: fd }).then(r => r.json());
  },

  // Watchlist
  watchlist: () => req("/portfolio/watchlist"),
  addWatch: (body) => req("/portfolio/watchlist", { method: "POST", body: JSON.stringify(body) }),
  removeWatch: (id) => req(`/portfolio/watchlist/${id}`, { method: "DELETE" }),

  // Market
  quote: (symbol) => req(`/market/quote/${symbol}`),
  marketHistory: (symbol, days = 365) => req(`/market/history/${symbol}?days=${days}`),
  search: (q) => req(`/market/search?q=${encodeURIComponent(q)}`),

  // News
  newsFeed: (minImportance = 0, symbol = "") =>
    req(`/news/feed?min_importance=${minImportance}${symbol ? `&symbol=${encodeURIComponent(symbol)}` : ""}`),
  newsRefresh: () => req("/news/refresh", { method: "POST" }),
  newsPortfolio: () => req("/news/portfolio"),
  newsSymbol: (symbol) => req(`/news/symbol/${symbol}`),
  newsWorld: () => req("/news/world"),

  // Alerts
  alerts: () => req("/alerts"),
  createAlert: (body) => req("/alerts", { method: "POST", body: JSON.stringify(body) }),
  updateAlert: (id, body) => req(`/alerts/${id}`, { method: "PATCH", body: JSON.stringify(body) }),
  deleteAlert: (id) => req(`/alerts/${id}`, { method: "DELETE" }),
  alertEvents: (unread = false) => req(`/alerts/events?unread_only=${unread}`),
  markAllRead: () => req("/alerts/events/read-all", { method: "POST" }),
  checkAlerts: () => req("/alerts/check", { method: "POST" }),
  refreshPrices: () => req("/alerts/refresh-prices", { method: "POST" }),

  // Research
  thesis: (params = "") => req(`/research/thesis${params}`),
  politicians: (params = "") => req(`/research/politicians${params}`),
  suggestions: (period = "daily") => req(`/research/suggestions?period=${period}`),
  suggestionsGenerate: (params = "") => req(`/research/suggestions/generate${params}`),
};
