"""Simple change-detection pipeline ("Demo Analysis").

Pipeline:
1. Load before/after images, resize to common dimensions.
2. Per-pixel mean absolute RGB difference.
3. Threshold at (mean + k * std), floored to avoid noise-only detections.
4. Connected-component labeling -> bounding boxes for top changed regions.
5. Pseudo-NDVI from green/red bands (synthetic data has no real NIR).

This is deliberately naive — a visual diff, not a scientific product — and
the UI labels results accordingly.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
from PIL import Image

ANALYSIS_SIZE = 256  # downsample before diffing; plenty for a demo
MIN_BOX_PIXELS = 40
MAX_BOXES = 8
DIFF_THRESHOLD_FLOOR = 0.07
THRESHOLD_K = 2.2


@dataclass
class ChangeBox:
    x: float  # normalized [0..1]
    y: float
    w: float
    h: float
    score: float  # mean diff inside the box


@dataclass
class AnalysisResult:
    changed_pct: float
    ndvi_before: float
    ndvi_after: float
    ndvi_change_pct: float
    mean_diff: float
    boxes: list[ChangeBox] = field(default_factory=list)
    channel_diffs: dict[str, float] = field(default_factory=dict)


def _to_array(img: Image.Image) -> np.ndarray:
    rgb = img.convert("RGB").resize((ANALYSIS_SIZE, ANALYSIS_SIZE))
    return np.asarray(rgb, dtype=np.float64) / 255.0


def _pseudo_ndvi(arr: np.ndarray) -> float:
    r, g = arr[..., 0], arr[..., 1]
    return float(((g - r) / (g + r + 1e-6)).mean())


def _find_boxes(mask: np.ndarray, diff: np.ndarray) -> list[ChangeBox]:
    """BFS connected-component labeling on the boolean mask."""
    h, w = mask.shape
    labels = np.zeros((h, w), dtype=np.int32)
    current = 0
    boxes: list[tuple[int, int, int, int, int]] = []  # x0,y0,x1,y1,count

    for y0 in range(h):
        xs = np.nonzero(mask[y0] & (labels[y0] == 0))[0]
        for x0 in xs:
            if labels[y0, x0]:
                continue
            current += 1
            stack = [(y0, x0)]
            labels[y0, x0] = current
            min_x = max_x = x0
            min_y = max_y = y0
            count = 0
            while stack:
                cy, cx = stack.pop()
                count += 1
                min_x, max_x = min(min_x, cx), max(max_x, cx)
                min_y, max_y = min(min_y, cy), max(max_y, cy)
                for ny, nx in ((cy - 1, cx), (cy + 1, cx), (cy, cx - 1), (cy, cx + 1)):
                    if 0 <= ny < h and 0 <= nx < w and mask[ny, nx] and not labels[ny, nx]:
                        labels[ny, nx] = current
                        stack.append((ny, nx))
            boxes.append((min_x, min_y, max_x, max_y, count))

    result = []
    for min_x, min_y, max_x, max_y, count in sorted(boxes, key=lambda b: -b[4]):
        if count < MIN_BOX_PIXELS or len(result) >= MAX_BOXES:
            continue
        region = diff[min_y:max_y + 1, min_x:max_x + 1]
        result.append(ChangeBox(
            x=min_x / w,
            y=min_y / h,
            w=(max_x - min_x + 1) / w,
            h=(max_y - min_y + 1) / h,
            score=float(region.mean()),
        ))
    return result


def detect_changes(before: Image.Image, after: Image.Image) -> AnalysisResult:
    b = _to_array(before)
    a = _to_array(after)

    diff = np.abs(a - b).mean(axis=2)
    threshold = max(diff.mean() + THRESHOLD_K * diff.std(), DIFF_THRESHOLD_FLOOR)
    mask = diff > threshold

    r_b, g_b = b[..., 0], b[..., 1]
    r_a, g_a = a[..., 0], a[..., 1]
    ndvi_before = float(((g_b - r_b) / (g_b + r_b + 1e-6)).mean())
    ndvi_after = float(((g_a - r_a) / (g_a + r_a + 1e-6)).mean())

    return AnalysisResult(
        changed_pct=float(mask.mean() * 100),
        ndvi_before=ndvi_before,
        ndvi_after=ndvi_after,
        ndvi_change_pct=float(
            ((ndvi_after - ndvi_before) / (abs(ndvi_before) + 1e-6)) * 100
        ),
        mean_diff=float(diff.mean()),
        boxes=_find_boxes(mask, diff),
        channel_diffs={
            "red": float(np.abs(a[..., 0] - b[..., 0]).mean()),
            "green": float(np.abs(a[..., 1] - b[..., 1]).mean()),
            "blue": float(np.abs(a[..., 2] - b[..., 2]).mean()),
        },
    )
