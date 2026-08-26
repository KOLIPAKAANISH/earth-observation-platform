"""Synthetic satellite-style scene generation for DEMO DATA.

Each (location, date) pair deterministically produces a small RGB image that
loosely resembles a top-down satellite view. Scenes are generated with a
hash-seeded RNG so the same request always returns the same pixels, and
temporal drift is baked in per scene kind so that different dates genuinely
differ (construction grows, farmland cycles crops, coastlines erode).
"""

from __future__ import annotations

import hashlib

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

SIZE = 384  # square output, keeps analysis fast


def _rng(*parts: object) -> np.random.Generator:
    digest = hashlib.sha256("|".join(str(p) for p in parts).encode()).digest()
    return np.random.default_rng(int.from_bytes(digest[:8], "big"))


def _date_index(date: str) -> float:
    """Turn 'YYYY-MM-DD' into a fractional year offset from 2024-01-01."""
    year, month, day = (int(x) for x in date.split("-"))
    return (year - 2024) + (month - 1) / 12 + (day - 1) / 365


def _add_noise(arr: np.ndarray, rng: np.random.Generator, sigma: float) -> np.ndarray:
    noise = rng.normal(0, sigma, arr.shape)
    return np.clip(arr + noise, 0, 255)


def _draw_fields(draw: ImageDraw.ImageDraw, rng: np.random.Generator, n: int,
                 palette: list[tuple[int, int, int]]) -> None:
    """Patchwork of agricultural fields."""
    x, y = 0, 0
    for i in range(n * 3):
        w = int(rng.integers(50, 130))
        h = int(rng.integers(40, 110))
        if i % 3 == 0:
            x, y = 0, y
        color = palette[int(rng.integers(0, len(palette)))]
        draw.rectangle([x, y, x + w, y + h], fill=color)
        x += w
        if x > SIZE:
            x, y = 0, y + h
        if y > SIZE:
            break


def generate_scene(location_id: str, kind: str, date: str) -> Image.Image:
    rng = _rng(location_id, kind, date)
    t = _date_index(date)

    # Base terrain per kind -------------------------------------------------
    if kind == "farmland":
        base = (86, 124, 66)
        field_palette = [
            (104, 144, 70), (140, 160, 80), (92, 118, 58),
            (168, 158, 96), (120, 132, 64),
        ]
    elif kind == "coast":
        base = (196, 182, 148)
        field_palette = [(188, 176, 142), (170, 164, 128)]
    else:  # construction / mixed urban ground
        base = (128, 122, 112)
        field_palette = [(120, 116, 106), (136, 130, 118)]

    img = Image.new("RGB", (SIZE, SIZE), base)
    draw = ImageDraw.Draw(img)

    # Water body (dominant for coast) --------------------------------------
    if kind == "coast":
        shoreline = int(SIZE * (0.42 - 0.035 * t))  # water encroaches over time
        draw.polygon(
            [(0, 0), (SIZE, 0), (SIZE, shoreline - 18),
             (int(SIZE * 0.7), shoreline), (int(SIZE * 0.4), shoreline - 10),
             (0, shoreline + 6)],
            fill=(38, 84, 122),
        )
    elif kind == "farmland":
        pass
    else:
        cx, cy = int(rng.integers(60, 100)), int(rng.integers(200, 260))
        r = int(28 + 4 * t)
        draw.ellipse([cx - r, cy - r // 2, cx + r, cy + r // 2], fill=(52, 96, 128))

    # Fields ----------------------------------------------------------------
    _draw_fields(draw, rng, 8, field_palette)

    # Re-stamp water on top for coasts so fields don't cover it -------------
    if kind == "coast":
        shoreline = int(SIZE * (0.42 - 0.035 * t))
        draw.polygon(
            [(0, 0), (SIZE, 0), (SIZE, shoreline - 18),
             (int(SIZE * 0.7), shoreline), (int(SIZE * 0.4), shoreline - 10),
             (0, shoreline + 6)],
            fill=(38, 84, 122),
        )

    # Kind-specific temporal features ---------------------------------------
    if kind == "construction":
        # Buildings appear and grow over time.
        n_buildings = 4 + max(0, int(t * 3))
        for i in range(n_buildings):
            bx = int(rng.integers(30, SIZE - 90))
            by = int(rng.integers(30, SIZE - 90))
            bw = int(rng.integers(28, 70))
            bh = int(rng.integers(24, 62))
            shade = int(rng.integers(120, 175))
            draw.rectangle([bx, by, bx + bw, by + bh],
                           fill=(shade, shade - 6, shade - 14))
            draw.rectangle([bx + 4, by + 4, bx + bw - 4, by + 10],
                           fill=(210, 190, 150))
            if t > 1.5:
                # second phase: an extra wing
                draw.rectangle([bx + bw, by + bh // 3, bx + bw + 22, by + bh],
                               fill=(shade - 15, shade - 20, shade - 26))

    if kind == "farmland":
        # Crop vigor oscillates seasonally: greener mid-year.
        seasonal = 0.5 + 0.5 * np.cos((t % 1.0) * 2 * np.pi)
        overlay = Image.new("RGB", (SIZE, SIZE),
                            (int(20 * seasonal), int(46 * seasonal), int(10 * seasonal)))
        img = Image.blend(img, overlay, alpha=0.28)

    if kind == "coast":
        # Beach width shrinks as water advances; add foam line.
        shoreline = int(SIZE * (0.42 - 0.035 * t))
        draw.line([(0, shoreline + 6), (int(SIZE * 0.4), shoreline - 4),
                   (int(SIZE * 0.7), shoreline + 6), (SIZE, shoreline - 12)],
                  fill=(232, 238, 240), width=3)

    # Roads / access lines ----------------------------------------------------
    for _ in range(2):
        x0 = int(rng.integers(0, SIZE))
        draw.line([(x0, 0), (x0 + int(rng.integers(-80, 80)), SIZE)],
                  fill=(105, 102, 98), width=6)

    # Sensor noise + slight blur so it reads as imagery, not clip-art --------
    arr = np.asarray(img).astype(np.float64)
    arr = _add_noise(arr, rng, sigma=9)
    img = Image.fromarray(arr.astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.7))
    return img
