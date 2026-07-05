// Store de trabajos de research a nivel de módulo: el estado y el sondeo viven
// FUERA de los componentes React, así que cambiar de pestaña o de página no
// reinicia nada. El backend deduplica por parámetros (patrón "attach"), de modo
// que aunque se recargue la página entera, relanzar la misma consulta se
// engancha al trabajo en curso o al resultado cacheado.
import { useSyncExternalStore } from "react";

const POLL_MS = 2500;

const stores = new Map(); // kind -> { state, subs, timer }

function ensure(kind) {
  if (!stores.has(kind)) {
    stores.set(kind, {
      state: { status: "idle", params: null, data: null, error: null, elapsed: 0 },
      subs: new Set(),
      timer: null,
    });
  }
  return stores.get(kind);
}

function setState(kind, patch) {
  const s = ensure(kind);
  s.state = { ...s.state, ...patch };
  s.subs.forEach((fn) => fn());
}

// `refresh=true` solo debe viajar en la PRIMERA petición (relanza el trabajo);
// si los sondeos siguientes lo repitieran, al terminar el trabajo lo
// relanzarían en bucle infinito.
function stripRefresh(params) {
  const qs = new URLSearchParams((params || "").replace(/^\?/, ""));
  qs.delete("refresh");
  const q = qs.toString();
  return q ? `?${q}` : "";
}

async function poll(kind, fetcher, sendParams, ownerParams) {
  const s = ensure(kind);
  let r;
  try {
    r = await fetcher(sendParams);
  } catch (e) {
    if (s.state.params === ownerParams) {
      setState(kind, { status: "error", error: e.message || String(e) });
    }
    return;
  }
  // Si mientras tanto el usuario lanzó otra consulta, este sondeo ya no manda.
  if (s.state.params !== ownerParams) return;

  if (r.status === "running") {
    setState(kind, { status: "running", elapsed: r.elapsed_seconds || 0 });
    s.timer = setTimeout(() => poll(kind, fetcher, stripRefresh(ownerParams), ownerParams), POLL_MS);
  } else if (r.status === "error") {
    setState(kind, { status: "error", error: r.error || "Error en el trabajo" });
  } else {
    setState(kind, { status: "done", data: r, error: null, elapsed: r.elapsed_seconds || 0 });
  }
}

/** Lanza (o re-engancha) un trabajo. `fetcher(params)` debe devolver el JSON del endpoint. */
export function startJob(kind, fetcher, params) {
  const s = ensure(kind);
  if (s.timer) { clearTimeout(s.timer); s.timer = null; }
  setState(kind, { status: "running", params, data: null, error: null, elapsed: 0 });
  poll(kind, fetcher, params, params);
}

/** Hook: suscribe el componente al estado del trabajo `kind`. */
export function useJob(kind) {
  const s = ensure(kind);
  return useSyncExternalStore(
    (cb) => { s.subs.add(cb); return () => s.subs.delete(cb); },
    () => s.state,
  );
}
