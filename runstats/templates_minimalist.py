from __future__ import annotations

from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.patheffects as pe

from .models import ActivityData, ActivitySummary
from .template_support import (
    draw_route_markers,
    font_props,
    make_figure,
    save_figure,
)
from .templates import TemplateStyle

_CORAL = "#ff734a"
_LIME = "#f3ffca"
_LIME_BRIGHT = "#cafd00"
_DARK = "#333333"
_DARK_MUTED = "#888888"


# ─── Format helpers ─────────────────────────────────────────────────────────

def _fmt_pace_colon(min_per_km: float) -> str:
    total_s = int(round(min_per_km * 60))
    m, s = divmod(total_s, 60)
    return f"{m:02d}:{s:02d}"


def _fmt_time_compact(seconds: float) -> str:
    """MM:SS when under 1 hour, H:MM:SS otherwise."""
    total_s = int(round(seconds))
    h, rem = divmod(total_s, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"



# ─── Main render ────────────────────────────────────────────────────────────

def render_minimalist_overlay(
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

    # Header: location only
    _draw_header(fig, activity, location)

    # Route
    if activity.point_count >= 2:
        route_ax = fig.add_axes([0.10, 0.32, 0.80, 0.55])
        _render_route(route_ax, activity)
        draw_route_markers(route_ax, activity, _CORAL, _LIME, marker_size=5)

    # Bottom metrics
    if summary is not None:
        _draw_hero_distance(fig, summary)
        _draw_stats_row(fig, summary)

    save_figure(fig, output_path, style)


# ─── Header ──────────────────────────────────────────────────────────────────

def _draw_header(fig, activity: ActivityData, location: str | None) -> None:
    if location:
        fig.text(
            0.5, 0.945,
            location.upper(),
            color=_CORAL, ha="center", va="center",
            fontproperties=font_props("bold", 13),
        )


# ─── Route ───────────────────────────────────────────────────────────────────

def _render_route(ax, activity: ActivityData) -> None:
    """Thin dashed coral route with subtle glow."""
    lons = activity.longitudes
    lats = activity.latitudes

    (line,) = ax.plot(
        lons, lats,
        color=_CORAL,
        linewidth=1.2,
        linestyle=(0, (4, 4)),
        dash_capstyle="round",
        solid_joinstyle="round",
        alpha=0.90,
        zorder=3,
    )
    line.set_path_effects([
        pe.withStroke(linewidth=5, foreground=(1.0, 0.451, 0.290, 0.12)),
        pe.withStroke(linewidth=3, foreground=(1.0, 0.451, 0.290, 0.25)),
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

    # Huge center-aligned orange number
    fig.text(
        0.50, 0.215,
        num_str,
        color=_CORAL,
        ha="center", va="center",
        fontproperties=font_props("heavy", 90),
    )

    # "KM" — pushed to the right edge
    fig.text(
        0.92, 0.255,
        "KM",
        color=_CORAL,
        ha="right", va="center",
        fontproperties=font_props("bold", 22),
    )


# ─── Secondary stats ─────────────────────────────────────────────────────────

def _draw_stats_row(fig, summary: ActivitySummary) -> None:
    """Two-column: PACE + MIN/KM | TIME — left-aligned, magazine style."""
    left_x = 0.08
    right_x = 0.52
    label_y = 0.138
    value_y = 0.102

    # ── PACE ──
    fig.text(
        left_x, label_y, "PACE",
        color=_DARK_MUTED, ha="left", va="center",
        fontproperties=font_props("bold", 10),
    )
    pace_str = _fmt_pace_colon(summary.avg_pace_min_per_km)
    fig.text(
        left_x, value_y, pace_str,
        color=_DARK, ha="left", va="center",
        fontproperties=font_props("medium", 30),
    )
    # "MIN/KM" coral suffix — placed below the pace value to avoid overlap
    fig.text(
        left_x, value_y - 0.028, "MIN/KM",
        color=_CORAL, ha="left", va="center",
        fontproperties=font_props("bold", 8),
    )

    # ── Vertical divider ──
    div_x = right_x - 0.025
    fig.lines.append(mlines.Line2D(
        [div_x, div_x],
        [label_y - 0.012, value_y + 0.022],
        transform=fig.transFigure,
        color=_DARK_MUTED,
        linewidth=0.5,
        alpha=0.3,
    ))

    # ── TIME ──
    fig.text(
        right_x, label_y, "TIME",
        color=_DARK_MUTED, ha="left", va="center",
        fontproperties=font_props("bold", 10),
    )
    fig.text(
        right_x, value_y,
        _fmt_time_compact(summary.moving_time_s),
        color=_DARK, ha="left", va="center",
        fontproperties=font_props("medium", 30),
    )

