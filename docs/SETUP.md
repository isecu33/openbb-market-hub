# Guía de instalación

## Requisitos previos

- Python 3.10–3.13
- Cuenta gratuita en [Financial Modeling Prep](https://site.financialmodelingprep.com/developer/docs) (clave API)
- Cuenta gratuita en [FRED](https://fred.stlouisfed.org/docs/api/api_key.html) (clave API)

## 1. Entorno virtual

```bash
python -m venv .venv
source .venv/bin/activate        # Windows PowerShell: .venv\Scripts\Activate.ps1
```

## 2. Dependencias

```bash
pip install -r requirements.txt
```

Esto instala OpenBB Platform, FastAPI/Uvicorn para el backend, y pandas/python-dotenv como utilidades. La instalación de OpenBB puede tardar varios minutos.

## 3. Claves API

```bash
cp .env.example .env
```

Edita `.env` y pega tus claves de FMP y FRED (los enlaces para sacarlas gratis están en el propio archivo).

## 4. Verificación

```bash
python scripts/setup_keys.py
```

Este script comprueba que `.env` existe, que las claves no están vacías, y hace una llamada de prueba a OpenBB.

## 5. Probar los tres casos de uso

```bash
python src/thesis_energy.py
python src/politician_tracker.py --build-watchlist
python src/portfolio_tracker.py --watchlist AAPL MSFT NVDA
```

## 6. Backend para OpenBB Workspace (opcional)

```bash
bash backend/run_backend.sh
```

Luego, en [pro.openbb.co](https://pro.openbb.co): **Apps → Connect backend → `http://localhost:8000`**.

## Notas sobre versiones de OpenBB

Los nombres exactos de algunos endpoints (especialmente el screener y `government.trades`) pueden cambiar entre versiones de OpenBB. Los scripts de este proyecto intentan varias rutas conocidas automáticamente y avisan si ninguna funciona. Si te encuentras con un error de "endpoint no encontrado", usa la skill `openbb-query` (o ejecuta `python .claude/skills/openbb-query/scripts/list_endpoints.py`) para descubrir el nombre real en tu instalación.

## Problemas frecuentes

- **`pip install` se queda colgado o tarda mucho**: es normal, OpenBB tiene muchas dependencias. Espera unos minutos; si falla, prueba `pip install --no-cache-dir -r requirements.txt`.
- **Error de clave API inválida**: revisa que copiaste la clave completa en `.env` sin comillas ni espacios.
- **`ModuleNotFoundError: No module named 'openbb'`**: asegúrate de tener el entorno virtual activado (`source .venv/bin/activate`) antes de ejecutar los scripts.
