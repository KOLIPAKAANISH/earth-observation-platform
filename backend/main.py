"""FastAPI app tying together the mock provider and the change-detection demo."""

from __future__ import annotations

import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from PIL import Image, ImageDraw
from pydantic import BaseModel

from analysis import detect_changes
from provider import AVAILABLE_DATES, DEMO_LOCATIONS, MockSatelliteProvider

CACHE_DIR = Path(__file__).parent / "cache"

app = FastAPI(title="Change Detection Demo API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

provider = MockSatelliteProvider(cache_dir=CACHE_DIR)


class AnalyzeRequest(BaseModel):
    location_id: str
    before_date: str
    after_date: str


@app.get("/api/locations")
async def list_locations() -> dict:
    return {
        "demo_data": True,
        "locations": [
            {
                "id": loc.id,
                "name": loc.name,
                "kind": loc.kind,
                "lat": loc.lat,
                "lon": loc.lon,
                "description": loc.description,
            }
            for loc in DEMO_LOCATIONS
        ],
        "available_dates": AVAILABLE_DATES,
    }


@app.get("/api/image/{location_id}/{date}")
async def get_image(location_id: str, date: str) -> FileResponse:
    try:
        await provider.get_image(location_id, date)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return FileResponse(CACHE_DIR / f"{location_id}_{date}.png", media_type="image/png")


@app.post("/api/analyze")
async def analyze(req: AnalyzeRequest) -> dict:
    if req.before_date == req.after_date:
        raise HTTPException(status_code=400, detail="Pick two different dates")
    try:
        before, after = await asyncio.gather(
            provider.get_image(req.location_id, req.before_date),
            provider.get_image(req.location_id, req.after_date),
        )
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc

    result = await asyncio.to_thread(detect_changes, before, after)
    overlay_path = await asyncio.to_thread(_build_overlay, after, result.boxes)
    overlay_name = f"overlay_{req.location_id}_{req.before_date}_{req.after_date}.png"
    (CACHE_DIR / overlay_name).unlink(missing_ok=True)
    await asyncio.to_thread(overlay_path.save, CACHE_DIR / overlay_name)

    return {
        "demo_data": True,
        "location_id": req.location_id,
        "before_date": req.before_date,
        "after_date": req.after_date,
        "stats": {
            "changed_pct": round(result.changed_pct, 2),
            "ndvi_before": round(result.ndvi_before, 4),
            "ndvi_after": round(result.ndvi_after, 4),
            "ndvi_change_pct": round(result.ndvi_change_pct, 2),
            "mean_diff": round(result.mean_diff, 4),
            "channel_diffs": {k: round(v, 4) for k, v in result.channel_diffs.items()},
        },
        "boxes": [
            {"x": b.x, "y": b.y, "w": b.w, "h": b.h, "score": round(b.score, 3)}
            for b in result.boxes
        ],
        "images": {
            "before": f"/api/image/{req.location_id}/{req.before_date}",
            "after": f"/api/image/{req.location_id}/{req.after_date}",
            "overlay": f"/api/image-cache/{overlay_name}",
        },
    }


def _build_overlay(after: Image.Image, boxes) -> Image.Image:
    """Copy of the 'after' image with change-region rectangles drawn on top."""
    img = after.convert("RGB").copy()
    draw = ImageDraw.Draw(img)
    w, h = img.size
    for i, box in enumerate(boxes):
        xy = [box.x * w, box.y * h, (box.x + box.w) * w, (box.y + box.h) * h]
        color = (255, 64, 64) if i % 2 == 0 else (255, 170, 0)
        for width in range(3, 0, -1):
            draw.rectangle(xy, outline=color, width=width)
        draw.text((xy[0] + 4, xy[1] + 3), f"#{i + 1}", fill=(255, 255, 255))
    return img


@app.get("/api/image-cache/{name}")
async def get_cached_image(name: str) -> FileResponse:
    # Only allow simple safe filenames from our own cache dir.
    if "/" in name or "\\" in name or ".." in name or not name.endswith(".png"):
        raise HTTPException(status_code=400, detail="Invalid filename")
    path = CACHE_DIR / name
    if not path.exists():
        raise HTTPException(status_code=404, detail="Not found")
    return FileResponse(path, media_type="image/png")


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "demo_data": True}
