from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .models import ActivityData, ActivitySummary


DEFAULT_TITLE = "RELENTLESS"
TEMPLATE_NAMES = ("story_overlay", "clean_card", "glass_slab", "clipboard_card", "neon_split")


@dataclass(frozen=True)
class TemplateStyle:
    canvas_width_px: int
    canvas_height_px: int
    dpi: int
    route_color: str = "#FF5500"
    text_color: str = "#FFFFFF"
    panel_color: str = "#101010"
    panel_alpha: float = 0.82
    title_color: str = "#FFFFFF"
    accent_color: str = "#FF5500"
    accent_alpha: float = 0.6


def render_template(
    template_name: str,
    activity: ActivityData,
    output_path: str | Path,
    route_mode: str,
    summary: ActivitySummary | None = None,
    title: str | None = DEFAULT_TITLE,
    location: str | None = None,
) -> None:
    if template_name == "story_overlay":
        from .templates_basic import render_story_overlay
        render_story_overlay(activity, output_path, route_mode, summary, title)
        return

    if template_name == "clean_card":
        from .templates_basic import render_clean_card
        render_clean_card(activity, output_path, route_mode, summary, title)
        return

    if template_name == "glass_slab":
        from .templates_glass import render_glass_slab
        render_glass_slab(activity, output_path, route_mode, summary, location)
        return

    if template_name == "clipboard_card":
        from .templates_clipboard import render_clipboard_card
        render_clipboard_card(activity, output_path, summary, location)
        return

    if template_name == "neon_split":
        from .templates_neon import render_neon_split
        render_neon_split(activity, output_path, route_mode, summary, location)
        return

    raise ValueError(f"Unknown template: {template_name}")


# ─────────────────────────────────────────────
# Shared gradient helpers (used by multiple templates)
# ─────────────────────────────────────────────


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def _diagonal_gradient_rgba(
    hex1: str,
    hex2: str,
    W: int,
    H: int,
    angle_deg: float,
    card_x0: float,
    card_y0: float,
    card_x1: float,
    card_y1: float,
    corner_r: float = 0.04,
) -> np.ndarray:
    """
    Create an RGBA image (H x W x 4) with a diagonal gradient inside a rounded-rectangle
    region and alpha=0 everywhere outside it.
    """
    c1 = np.array(_hex_to_rgb(hex1))
    c2 = np.array(_hex_to_rgb(hex2))

    xx = np.linspace(0, 1, W)
    yy = np.linspace(0, 1, H)
    XX, YY = np.meshgrid(xx, yy)
    rad = math.radians(angle_deg)
    t = XX * math.cos(rad) + (1.0 - YY) * math.sin(rad)
    t = (t - t.min()) / (t.max() - t.min() + 1e-9)

    rgb = c1[None, None, :] * (1 - t[:, :, None]) + c2[None, None, :] * t[:, :, None]

    # rounded-rectangle alpha mask
    px0, py0 = int(card_x0 * W), int(card_y0 * H)
    px1, py1 = int(card_x1 * W), int(card_y1 * H)
    pr = int(corner_r * min(W, H))

    mask = np.zeros((H, W), dtype=float)
    mask[py0 + pr : py1 - pr, px0:px1] = 1.0
    mask[py0:py1, px0 + pr : px1 - pr] = 1.0
    for cx, cy in [
        (px0 + pr, py0 + pr),
        (px1 - pr, py0 + pr),
        (px0 + pr, py1 - pr),
        (px1 - pr, py1 - pr),
    ]:
        ys = np.arange(max(0, cy - pr), min(H, cy + pr))
        xs = np.arange(max(0, cx - pr), min(W, cx + pr))
        YY2, XX2 = np.meshgrid(ys, xs, indexing="ij")
        inside = (XX2 - cx) ** 2 + (YY2 - cy) ** 2 <= pr ** 2
        mask[ys[0] : ys[-1] + 1, xs[0] : xs[-1] + 1] = np.maximum(
            mask[ys[0] : ys[-1] + 1, xs[0] : xs[-1] + 1], inside.astype(float)
        )

    rgba = np.zeros((H, W, 4), dtype=float)
    rgba[:, :, :3] = np.clip(rgb, 0, 1)
    rgba[:, :, 3] = mask
    return rgba


def _horiz_gradient_img(hex1: str, hex2: str, W: int = 512) -> np.ndarray:
    """1 x W x 3 horizontal gradient array."""
    c1 = np.array(_hex_to_rgb(hex1))
    c2 = np.array(_hex_to_rgb(hex2))
    t = np.linspace(0, 1, W)
    img = c1[None, :] * (1 - t[:, None]) + c2[None, :] * t[:, None]
    return np.clip(img, 0, 1)[None, :, :]
