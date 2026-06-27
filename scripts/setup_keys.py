"""
scripts/setup_keys.py
======================
Verifica que las claves API definidas en .env funcionan, antes de lanzarte
a usar los scripts principales.

Uso:
    python scripts/setup_keys.py
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")

REQUIRED_KEYS = {
    "FMP_API_KEY": "https://site.financialmodelingprep.com/developer/docs (plan gratuito disponible)",
    "FRED_API_KEY": "https://fred.stlouisfed.org/docs/api/api_key.html (gratuito)",
}


def check_env_file():
    env_path = ROOT / ".env"
    if not env_path.exists():
        print(f"No existe {env_path}. Copia .env.example a .env primero:\n  cp .env.example .env")
        sys.exit(1)


def check_keys():
    missing = []
    for key, where in REQUIRED_KEYS.items():
        value = os.getenv(key)
        if not value or value.startswith("tu_clave") or value.startswith("your_"):
            missing.append((key, where))

    if missing:
        print("Faltan claves por configurar en .env:")
        for key, where in missing:
            print(f"  - {key}  ->  consíguela en: {where}")
        sys.exit(1)
    print("Todas las claves requeridas están presentes en .env.")


def check_openbb_credentials():
    try:
        from openbb import obb
    except ImportError:
        print("OpenBB no está instalado. Ejecuta: pip install -r requirements.txt")
        sys.exit(1)

    try:
        obb.user.credentials.fmp_api_key = os.getenv("FMP_API_KEY")
        obb.user.credentials.fred_api_key = os.getenv("FRED_API_KEY")
        print("Credenciales cargadas en la sesión de OpenBB correctamente.")
    except Exception as e:  # noqa: BLE001
        print(f"Aviso: no se pudieron fijar las credenciales en OpenBB ({e}). "
              "Puede que los nombres de atributo cambien entre versiones; "
              "revisa `obb.user.credentials?` para ver los nombres exactos.")


def quick_smoke_test():
    try:
        from openbb import obb
        quote = obb.equity.price.quote(symbol="AAPL")
        print("Prueba rápida OK: se obtuvo cotización de AAPL.")
        return quote
    except Exception as e:  # noqa: BLE001
        print(f"Aviso: la prueba rápida con AAPL falló ({e}). "
              "Revisa tu clave de FMP o tu conexión a internet.")


if __name__ == "__main__":
    check_env_file()
    check_keys()
    check_openbb_credentials()
    quick_smoke_test()
