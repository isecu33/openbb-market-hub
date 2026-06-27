---
name: openbb-query
description: Ayuda a escribir y depurar consultas a la plataforma OpenBB en este proyecto. Útil cuando el nombre exacto de un endpoint no está claro o cambia entre versiones, o cuando una consulta a obb.* falla con un error de atributo/endpoint no encontrado.
---

# openbb-query

Esta skill ayuda a escribir y depurar llamadas a `obb.*` dentro de este proyecto.

## Cuándo usarla

- Al escribir una consulta nueva a OpenBB y no estás seguro del nombre exacto del endpoint.
- Cuando una llamada falla con `AttributeError` o un error de "endpoint no encontrado".
- Para explorar qué proveedores (FMP, FRED, etc.) soportan un endpoint dado.

## Cómo proceder

1. Ejecuta `python .claude/skills/openbb-query/scripts/list_endpoints.py <ruta_parcial>` para listar los endpoints reales disponibles que coincidan, en vez de adivinar el nombre.
2. Si el endpoint existe pero falla, revisa los parámetros con `obb.<ruta>.about()` o `help(obb.<ruta>)` dentro de una sesión de Python.
3. Sigue el patrón ya usado en `src/*.py`: envuelve la llamada en un intento con manejo de errores y, si hay varias rutas plausibles, pruébalas en orden (ver `_try_endpoints` en `thesis_energy.py` o `_fetch_government_trades` en `politician_tracker.py`).
4. Nunca hardcodees una clave API en el código — siempre vía `.env` / `os.getenv`.

## Notas

Los nombres de endpoints de OpenBB cambian entre versiones mayores. Esta skill prioriza descubrir el nombre real sobre confiar en lo que diga la documentación o el entrenamiento del modelo, que puede estar desactualizado.
