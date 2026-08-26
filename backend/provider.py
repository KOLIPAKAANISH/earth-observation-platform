"""Satellite imagery provider abstraction + mock implementation (DEMO DATA).

The `SatelliteProvider` interface is the seam where a real Sentinel-2 /
Landsat integration would plug in later. For this demo, images are generated
synthetically and cached on disk.
"""

from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path

from PIL import Image

from scene_gen import generate_scene


@dataclass(frozen=True)
class DemoLocation:
    id: str
    name: str
    kind: str  # construction | farmland | coast
    lat: float
    lon: float
    description: str


DEMO_LOCATIONS: list[DemoLocation] = [
    DemoLocation(
        id="riverside-construction",
        name="Riverside Construction Site",
        kind="construction",
        lat=30.2672,
        lon=-97.7431,
        description="Urban infill project near downtown Austin, TX (demo).",
    ),
    DemoLocation(
        id="central-valley-farmland",
        name="Central Valley Farmland",
        kind="farmland",
        lat=36.7378,
        lon=-119.7871,
        description="Row-crop fields outside Fresno, CA (demo).",
    ),
    DemoLocation(
        id="outer-banks-coast",
        name="Coastal Erosion Zone",
        kind="coast",
        lat=35.9450,
        lon=-75.6330,
        description="Shoreline retreat along the Outer Banks, NC (demo).",
    ),
]

AVAILABLE_DATES: list[str] = [
    "2024-03-15",
    "2024-06-15",
    "2024-09-15",
    "2024-12-15",
    "2025-03-15",
    "2025-06-15",
]


class SatelliteProvider(ABC):
    """Interface so a real Sentinel-2/Landsat provider can be swapped in later."""

    @abstractmethod
    async def get_image(self, location_id: str, date: str) -> Image.Image:
        """Return an RGB image of `location_id` captured on `date`."""


class MockSatelliteProvider(SatelliteProvider):
    """Generates synthetic imagery locally. Everything it returns is DEMO DATA."""

    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _locations(self) -> dict[str, DemoLocation]:
        return {loc.id: loc for loc in DEMO_LOCATIONS}

    async def get_image(self, location_id: str, date: str) -> Image.Image:
        loc = self._locations().get(location_id)
        if loc is None:
            raise KeyError(f"Unknown location: {location_id}")
        if date not in AVAILABLE_DATES:
            raise KeyError(f"Date {date} not in mock archive")

        cache_path = self.cache_dir / f"{location_id}_{date}.png"
        if cache_path.exists():
            return Image.open(cache_path).convert("RGB")

        # Scene generation is CPU work; keep the event loop responsive.
        img = await asyncio.to_thread(generate_scene, location_id, loc.kind, date)
        await asyncio.to_thread(img.save, cache_path)
        return img
