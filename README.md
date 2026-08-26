# Satellite Change-Detection Demo

A lightweight prototype of an earth-observation change-detection tool.
**All imagery is synthetic DEMO DATA** — no real satellite APIs are used.

## Stack
- **Backend**: Python + FastAPI (`backend/`) — mock satellite provider + naive pixel-diff change detection
- **Frontend**: Next.js + TypeScript + Tailwind CSS + MapLibre GL + Recharts (`frontend/`)

## Run it

Terminal 1 — backend:
```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

Terminal 2 — frontend:
```bash
cd frontend
npm install
npm run dev
```

Open http://localhost:3000, click a demo location marker, pick two dates,
and hit **Run Analysis**.

## What's inside
- `SatelliteProvider` interface (`backend/provider.py`) so a real Sentinel-2/Landsat provider can be swapped in later; `MockSatelliteProvider` generates deterministic synthetic scenes per (location, date) and caches them on disk.
- Change detection (`backend/analysis.py`): resize → per-pixel RGB abs diff → threshold (mean + k·std) → connected components → bounding boxes, plus a pseudo-NDVI (green vs red) since the synthetic data has no real NIR band.
- Endpoints: `GET /api/locations`, `GET /api/image/{loc}/{date}`, `POST /api/analyze`.

Out of scope for this version (parked for v2): auth, PostGIS, real satellite APIs, job queues, alerting, reports, Docker, ML models.
