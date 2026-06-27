---
name: politician-watchlist
description: Ayuda a consultar los Government Trades del Congreso de EE. UU. (Senado + Cámara) y a construir una watchlist espejo a partir de ellos. Útil al trabajar con src/politician_tracker.py.
---

# politician-watchlist

Esta skill cubre el trabajo con datos de Government Trades (operaciones divulgadas por congresistas de EE. UU.) en este proyecto.

## Regla no negociable

**Siempre** que se muestren, resuman o interpreten estos datos, hay que recordar que la STOCK Act permite hasta 45 días de retraso entre la operación real y su divulgación pública. Nunca lo presentes como señal de timing de mercado en tiempo real. El propio `politician_tracker.py` imprime este aviso (`print_disclosure_warning`) — no lo elimines si modificas el script.

## Cómo proceder

1. Si el endpoint de Government Trades cambia de nombre entre versiones de OpenBB, usa la skill `openbb-query` (`list_endpoints.py`) para localizar el nombre real bajo `obb.equity.ownership` o `obb.regulators`, en vez de asumir el de una versión anterior.
2. Para construir una watchlist espejo, cuenta frecuencia de operaciones por ticker (`build_mirror_watchlist`) y deja que el usuario ajuste el umbral mínimo (`--min-trades`).
3. Filtrar por político concreto (`--politician "Nombre Apellido"`) es útil, pero ten en cuenta que la coincidencia de nombres puede ser imprecisa según el proveedor de datos — si los resultados parecen vacíos o erróneos, sugiere revisar el nombre exacto que usa el proveedor.
4. No conviertas esto en una herramienta de "copiar operaciones de políticos" sin el aviso de retraso visible en cualquier salida (consola, API, informe).
