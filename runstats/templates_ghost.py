from __future__ import annotations

from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import numpy as np

from .models import ActivityData, ActivitySummary
from .template_support import (
    draw_route_markers,
    font_props,
    make_figure,
    save_figure,
)
from .templates import TemplateStyle, _hex_to_rgb

_CORAL = "#ff734a"
_LIME = "#f3ffca"
_SURFACE_VAR = (0.149, 0.149, 0.149)  # #262626


# ─── Format helpers ─────────────────────────────────────────────────────────

def _fmt_pace_colon(min_per_km: float) -> str:
    """MM:SS format (e.g. '05:30')."""
    total_s = int(round(min_per_km * 60))
    m, s = divmod(total_s, 60)
    return f"{m:02d}:{s:02d}"


def _fmt_hhmmss(seconds: float) -> str:
    """Always HH:MM:SS (e.g. '00:57:45')."""
    total_s = int(round(seconds))
    h, rem = divmod(total_s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


# ─── Main render ────────────────────────────────────────────────────────────

def render_ghost_overlay(
    activity: ActivityData,
    output_path: str | Path,
    route_mode: str,
    summary: ActivitySummary | None,
    location: str | None = None,
) -> None:
    style = TemplateStyle(
        canvas_width_px=1080,
        canvas_height_px=1920,
        dpi=200,
        route_color=_CORAL,
        accent_color=_CORAL,
    )
    fig = make_figure(style)
    W, H = style.canvas_width_px, style.canvas_height_px

    # Dark base — simulates photo at brightness-[0.4]
    base_arr = np.zeros((2, 2, 4))
    base_arr[:, :, 3] = 0.62
    base_ax = fig.add_axes([0, 0, 1, 1])
    base_ax.imshow(base_arr, aspect="auto", extent=[0, 1, 0, 1], origin="upper")
    base_ax.axis("off")

    # Vignette
    _draw_vignette(fig)

    # Top bar
    _draw_top_bar(fig, location)

    # GPS route
    if activity.point_count >= 2:
        route_ax = fig.add_axes([0.14, 0.36, 0.72, 0.55])
        _render_glowing_route(route_ax, activity)
        draw_route_markers(route_ax, activity, _CORAL, _LIME, marker_size=7)

    # Hero distance + glass card
    if summary is not None:
        _draw_hero_distance(fig, summary)
        _draw_glass_card(fig, summary)

    save_figure(fig, output_path, style)


# ─── Vignette ────────────────────────────────────────────────────────────────

def _draw_vignette(fig) -> None:
    # Top: surface/40 → transparent
    top_a = np.linspace(0.40, 0.0, 256)
    top_rgba = np.zeros((256, 1, 4))
    top_rgba[:, 0, 3] = top_a
    top_ax = fig.add_axes([0, 0.85, 1, 0.15])
    top_ax.imshow(top_rgba, aspect="auto", extent=[0, 1, 0, 1], origin="upper")
    top_ax.axis("off")

    # Bottom: transparent → surface/80
    bot_a = np.linspace(0.0, 0.80, 256)
    bot_rgba = np.zeros((256, 1, 4))
    bot_rgba[:, 0, 3] = bot_a
    bot_ax = fig.add_axes([0, 0, 1, 0.25])
    bot_ax.imshow(bot_rgba, aspect="auto", extent=[0, 1, 0, 1], origin="lower")
    bot_ax.axis("off")


# ─── Top bar ─────────────────────────────────────────────────────────────────

def _draw_top_bar(fig, location: str | None) -> None:
    fig.text(
        0.5, 0.960,
        location.upper() if location else "",
        color=(1, 1, 1, 0.90), ha="center", va="center",
        fontproperties=font_props("bold", 15),
    )


# ─── GPS route ───────────────────────────────────────────────────────────────

def _render_glowing_route(ax, activity: ActivityData) -> None:
    """Tight-dotted coral route with soft glow."""
    lons = activity.longitudes
    lats = activity.latitudes

    (line,) = ax.plot(
        lons, lats,
        color=_CORAL,
        linewidth=2.0,
        linestyle=(0, (2, 3)),
        dash_capstyle="round",
        solid_joinstyle="round",
        alpha=0.92,
        zorder=3,
    )
    line.set_path_effects([
        pe.withStroke(linewidth=8, foreground=(1.0, 0.451, 0.290, 0.12)),
        pe.withStroke(linewidth=4, foreground=(1.0, 0.451, 0.290, 0.30)),
        pe.Normal(),
    ])

    lon_min, lon_max = min(lons), max(lons)
    lat_min, lat_max = min(lats), max(lats)
    w = max(lon_max - lon_min, 1e-9)
    h = max(lat_max - lat_min, 1e-9)
    ax.set_xlim(lon_min - w * 0.06, lon_max + w * 0.06)
    ax.set_ylim(lat_min - h * 0.06, lat_max + h * 0.06)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.patch.set_alpha(0.0)


# ─── Hero distance ───────────────────────────────────────────────────────────

def _draw_hero_distance(fig, summary: ActivitySummary) -> None:
    num_str = f"{summary.distance_km:.2f}"

    # "DISTANCE" micro-label
    fig.text(
        0.5, 0.325,
        "DISTANCE",
        color=(1, 1, 1, 0.50),
        ha="center", va="center",
        fontproperties=font_props("bold", 11),
    )

    # Big white number
    fig.text(
        0.5, 0.255,
        num_str,
        color="#FFFFFF",
        ha="center", va="center",
        fontproperties=font_props("heavy", 72),
    )

    # "KM" lime suffix
    km_x = 0.5 + len(num_str) * 0.054 + 0.020
    fig.text(
        km_x, 0.240,
        "KM",
        color=_LIME,
        ha="left", va="center",
        fontproperties=font_props("bold", 22),
    )


# ─── Frosted glass stats card ────────────────────────────────────────────────

def _draw_glass_card(fig, summary: ActivitySummary) -> None:
    """Compact two-column glass card: AVG PACE | TIME."""
    card_x, card_y = 0.065, 0.060
    card_w, card_h = 0.870, 0.118

    glass_ax = fig.add_axes([0, 0, 1, 1])
    glass_ax.axis("off")
    glass_ax.patch.set_alpha(0.0)

    # Glass surface
    glass_ax.add_patch(mpatches.FancyBboxPatch(
        (card_x, card_y), card_w, card_h,
        boxstyle="round,pad=0.008,rounding_size=0.032",
        facecolor=(*_SURFACE_VAR, 0.45),
        edgecolor=(1, 1, 1, 0.10),
        linewidth=0.8,
        transform=glass_ax.transAxes,
    ))

    # Column divider
    div_x = card_x + card_w / 2
    fig.lines.append(mlines.Line2D(
        [div_x, div_x],
        [card_y + 0.015, card_y + card_h - 0.015],
        transform=fig.transFigure,
        color=(1, 1, 1, 0.10),
        linewidth=0.7,
    ))

    label_y = card_y + card_h * 0.75
    value_y = card_y + card_h * 0.28
    left_cx = card_x + card_w * 0.25
    right_cx = card_x + card_w * 0.75

    # Left: AVG PACE
    fig.text(
        left_cx, label_y, "AVG PACE",
        color=_CORAL, ha="center", va="center",
        fontproperties=font_props("bold", 9),
    )
    pace_str = _fmt_pace_colon(summary.avg_pace_min_per_km)
    fig.text(
        left_cx - 0.030, value_y, pace_str,
        color="#FFFFFF", ha="center", va="center",
        fontproperties=font_props("semibold", 22),
    )
    fig.text(
        left_cx + 0.055, value_y - 0.003, "/KM",
        color=(1, 1, 1, 0.35), ha="left", va="center",
        fontproperties=font_props("regular", 10),
    )

    # Right: TIME
    fig.text(
        right_cx, label_y, "TIME",
        color=(1, 1, 1, 0.50), ha="center", va="center",
        fontproperties=font_props("bold", 9),
    )
    fig.text(
        right_cx, value_y,
        _fmt_hhmmss(summary.moving_time_s),
        color="#FFFFFF", ha="center", va="center",
        fontproperties=font_props("semibold", 22),
    )
