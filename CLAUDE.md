# CLAUDE.md

Contexto de proyecto para Claude Code/Desktop. Este archivo se carga automáticamente cuando trabajas dentro de este repositorio.

## Qué es este proyecto

Plataforma personal de research de inversiones, autoalojada, sobre OpenBB Platform. **No** sustituye al bróker (MyInvestor) para precios en vivo ni ejecución — es solo research: noticias, sentimiento, tesis temáticas y tracking de operaciones de políticos.

## Los tres casos de uso (no los mezcles conceptualmente)

1. `src/thesis_energy.py` — de hipótesis macro a lista corta de candidatas.
2. `src/politician_tracker.py` — Government Trades (Senado + Cámara), proveedor FMP. **Siempre** recuerda el retraso de hasta 45 días de la STOCK Act al mostrar o interpretar estos datos.
3. `src/portfolio_tracker.py` — watchlist/cartera con noticias, alimentada manualmente vía CSV (MyInvestor no tiene API pública).

## Convenciones del repo

- Cada script es ejecutable de forma independiente vía `argparse`, y también se expone como endpoint en `backend/app.py`.
- Los endpoints de OpenBB pueden cambiar de nombre entre versiones. Los scripts ya manejan esto con `_try_endpoints` / bloques try-except con rutas alternativas — sigue ese patrón si añades nuevas consultas, no asumas que un nombre de endpoint es estable.
- Las claves API viven solo en `.env` (nunca en el código ni en commits). `.env.example` documenta qué claves hacen falta y dónde sacarlas gratis.
- MIT License. Cambios que añadan dependencias deben reflejarse en `requirements.txt`.

## Skills disponibles en este repo

- **openbb-query** — para escribir/depurar consultas a OpenBB, incluye `list_endpoints.py` para descubrir endpoints reales sin adivinar.
- **thesis-builder** — guía el flujo de tesis temática → candidatas, con la regla de señalar cuándo los datos contradicen la tesis.
- **politician-watchlist** — para trabajar con Government Trades y vigilar siempre el aviso de los 45 días de retraso.

## Cómo ayudar en este proyecto

- Si el usuario pide una nueva consulta a OpenBB y no estás seguro del endpoint exacto, usa primero `list_endpoints.py` en vez de adivinar.
- Si tocas `politician_tracker.py`, no elimines el aviso de la STOCK Act.
- Si añades un cuarto caso de uso, sigue el mismo patrón: script independiente en `src/`, expuesto también en `backend/app.py`, con su propio bloque en el README.
