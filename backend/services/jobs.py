"""
backend/services/jobs.py
========================
Gestor de trabajos en segundo plano para consultas lentas (p. ej. el screener
de tesis, que hace varias llamadas API por ticker y puede tardar minutos).

Patrón "attach": el endpoint llama a `get_or_submit(key, fn)` y devuelve al
instante un snapshot con el estado. La primera petición lanza el trabajo en un
hilo; las siguientes con los mismos parámetros se ENGANCHAN al trabajo en curso
(no lo relanzan) o reciben el resultado cacheado. Así el frontend puede
sondear, navegar a otra pestaña y volver sin reiniciar nada.

Todo vive en memoria del proceso: si el backend se reinicia, los trabajos se
pierden (aceptable para una app personal; los resultados se recalculan).
"""

from __future__ import annotations

import hashlib
import json
import os
import time
from concurrent.futures import ThreadPoolExecutor
from threading import Lock
from typing import Any, Callable

# Máximo de trabajos pesados simultáneos: los screeners saturan la cuota del
# proveedor si corren en paralelo, así que se encolan de dos en dos.
_executor = ThreadPoolExecutor(max_workers=2, thread_name_prefix="research-job")
_jobs: dict[str, dict] = {}
_lock = Lock()

# Cuánto tiempo sirve un resultado terminado sin recalcular.
RESULT_TTL_SECONDS = int(os.getenv("JOB_RESULT_TTL", "900"))
# Los errores se reintentan antes (suelen ser fallos transitorios del proveedor).
ERROR_TTL_SECONDS = 60


def make_key(name: str, params: dict) -> str:
    canonical = json.dumps(params, sort_keys=True, default=str)
    return f"{name}:{hashlib.sha1(canonical.encode()).hexdigest()[:16]}"


def _snapshot(job: dict) -> dict:
    now = time.time()
    out = {
        "job_key": job["key"],
        "status": job["status"],
        "started_at": job["started_at"],
        "elapsed_seconds": round((job.get("finished_at") or now) - job["started_at"], 1),
    }
    if job["status"] == "done":
        out["result"] = job["result"]
        out["cached_seconds"] = round(now - job["finished_at"], 1)
    elif job["status"] == "error":
        out["error"] = job["error"]
    return out


def _run(key: str, fn: Callable[[], Any]) -> None:
    try:
        result = fn()
        with _lock:
            job = _jobs.get(key)
            if job is not None:
                job.update(status="done", result=result, finished_at=time.time())
    except Exception as e:  # noqa: BLE001 - el error se entrega al cliente en el snapshot
        with _lock:
            job = _jobs.get(key)
            if job is not None:
                job.update(status="error", error=str(e), finished_at=time.time())


def get_or_submit(key: str, fn: Callable[[], Any], *, refresh: bool = False) -> dict:
    """Devuelve el snapshot del trabajo, lanzándolo solo si hace falta."""
    with _lock:
        job = _jobs.get(key)
        if job is not None:
            if job["status"] == "running":
                return _snapshot(job)
            age = time.time() - job["finished_at"]
            ttl = RESULT_TTL_SECONDS if job["status"] == "done" else ERROR_TTL_SECONDS
            if not refresh and age < ttl:
                return _snapshot(job)

        job = {"key": key, "status": "running", "started_at": time.time()}
        _jobs[key] = job
        _executor.submit(_run, key, fn)
        return _snapshot(job)


def get(key: str) -> dict | None:
    with _lock:
        job = _jobs.get(key)
        return _snapshot(job) if job else None
