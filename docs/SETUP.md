# Setup detallado

## 1. Requisitos

- Python 3.10+
- Node.js 18+ (para el frontend React)
- Claves API gratuitas: FMP y FRED.

## 2. Claves API

Copia `.env.example` a `.env` y rellena:

- `FMP_API_KEY` — https://site.financialmodelingprep.com/developer/docs
- `FRED_API_KEY` — https://fred.stlouisfed.org/docs/api/api_key.html

Opcionales: `PORT`, `BASE_CURRENCY`, `PRICE_REFRESH_MINUTES`, `ALERT_CHECK_MINUTES`.

Verifica las claves: `python scripts/setup_keys.py`.

## 3. Backend

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## 4. Frontend

```bash
cd frontend
npm install
npm run build      # genera frontend/dist (lo sirve el backend)
# o, en desarrollo con recarga:
npm run dev        # http://localhost:5173, proxya /api -> :8000
```

> Si vienes de una versión anterior y `frontend/node_modules` da problemas,
> bórralo y vuelve a ejecutar `npm install`.

## 5. Arrancar

```bash
uvicorn backend.app:app --reload      # todo en http://localhost:8000
```

En Windows puedes usar directamente `start.ps1` (producción) o `start-dev.ps1`
(desarrollo).

## 6. Importar tu cartera de MyInvestor

1. Exporta tu cartera o tus movimientos desde MyInvestor (CSV o Excel).
2. En la web, ve a **Importar**, sube el archivo y revisa la vista previa.
3. Confirma. Se detectan fondos (ISIN), acciones/ETF y movimientos
   automáticamente.

## 7. Alertas en segundo plano

Mientras el backend esté arrancado, el scheduler refresca precios y evalúa
alertas. Para dispararlo desde el Programador de tareas de Windows:

```
POST http://localhost:8000/api/alerts/refresh-prices
POST http://localhost:8000/api/alerts/check
```

## 8. OpenBB Workspace (opcional)

Conecta el backend desde https://pro.openbb.co (Apps → Connect backend →
`http://localhost:8000`). Los endpoints legacy `/thesis`, `/politician-trades` y
`/portfolio` siguen disponibles.
