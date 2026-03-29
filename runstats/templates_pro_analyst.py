from __future__ import annotations

from pathlib import Path

import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import numpy as np

from .models import ActivityData, ActivitySummary
from .template_support import (
    draw_icon_shape,
    font_props,
    make_figure,
    save_figure,
)
from .templates import TemplateStyle, _hex_to_rgb

# ─── Design tokens (from "The Kinetic Pulse" spec) ──────────────────────────

_ORANGE = "#FF8F6F"          # Primary (Electric Orange)
_SILVER = "#E2E2E2"          # Secondary (Cool Silver)
_SURFACE_HIGH = "#1F1F1F"    # Surface-Container-High
_GHOST_BORDER = (1, 1, 1, 0.15)  # 15 % white shimmer edge


# ─── Format helpers ──────────────────────────────────────────────────────────

def _fmt_pace_colon(min_per_km: float) -> str:
    total_s = int(round(min_per_km * 60))
    m, s = divmod(total_s, 60)
    return f"{m:02d}:{s:02d}"


def _fmt_hhmmss(seconds: float) -> str:
    total_s = int(round(seconds))
    h, rem = divmod(total_s, 3600)
    m, s = divmod(rem, 60)
    return f"{h:02d}:{m:02d}:{s:02d}"


# ─── Main render ─────────────────────────────────────────────────────────────

def render_pro_analyst(
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
        route_color=_ORANGE,
        accent_color=_ORANGE,
    )
    fig = make_figure(style)

    # GPS route (solid line)
    if activity.point_count >= 2:
        route_ax = fig.add_axes([0.10, 0.44, 0.80, 0.42])
        _render_route(route_ax, activity)

    # Hero distance
    if summary is not None:
        _draw_hero_distance(fig, summary)

    # Pace + Time row
    if summary is not None:
        _draw_pace_time_row(fig, summary)

    # Bottom data cards (elevation + avg heart rate)
    if summary is not None:
        _draw_bottom_cards(fig, summary)

    # Location at very bottom, centered
    _draw_location_footer(fig, location)

    save_figure(fig, output_path, style)


# ─── Location footer — bottom center ────────────────────────────────────────

def _draw_location_footer(fig, location: str | None) -> None:
    if not location:
        return

    badge_ax = fig.add_axes([0, 0, 1, 1])
    badge_ax.axis("off")
    badge_ax.patch.set_alpha(0.0)

    # Pin dot to the left of text
    fig.text(
        0.5, 0.030,
        location.upper(),
        color=_ORANGE,
        ha="center", va="center",
        fontproperties=font_props("bold", 10),
    )


# ─── GPS route ──────────────────────────────────────────────────────────────

def _render_route(ax, activity: ActivityData) -> None:
    lons = activity.longitudes
    lats = activity.latitudes

    # Soft wide halo
    ax.plot(
        lons, lats,
        color=(1, 1, 1, 0.04),
        linewidth=14,
        solid_capstyle="round",
        solid_joinstyle="round",
        zorder=1,
    )

    # Main route — solid line
    r, g, b = _hex_to_rgb(_ORANGE)
    (line,) = ax.plot(
        lons, lats,
        color=_ORANGE,
        linewidth=2.8,
        solid_capstyle="round",
        solid_joinstyle="round",
        alpha=0.92,
        zorder=3,
    )
    line.set_path_effects([
        pe.withStroke(linewidth=10, foreground=(r, g, b, 0.06)),
        pe.withStroke(linewidth=6, foreground=(r, g, b, 0.18)),
        pe.Normal(),
    ])

    # Start marker
    ax.plot(lons[0], lats[0], "o", color=_ORANGE,
            markersize=6, zorder=5, markeredgewidth=0)

    # End marker
    ax.plot(lons[-1], lats[-1], "s", color=_SILVER,
            markersize=4, zorder=5, markeredgewidth=0)

    lon_min, lon_max = min(lons), max(lons)
    lat_min, lat_max = min(lats), max(lats)
    w = max(lon_max - lon_min, 1e-9)
    h = max(lat_max - lat_min, 1e-9)
    ax.set_xlim(lon_min - w * 0.08, lon_max + w * 0.08)
    ax.set_ylim(lat_min - h * 0.08, lat_max + h * 0.08)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.patch.set_alpha(0.0)


# ─── Hero distance ──────────────────────────────────────────────────────────

def _draw_hero_distance(fig, summary: ActivitySummary) -> None:
    # More vertical gap between "DISTANCE" and the number
    fig.text(
        0.5, 0.430,
        "DISTANCE",
        color=_ORANGE,
        ha="center", va="center",
        fontproperties=font_props("bold", 10),
    )

    num_str = f"{summary.distance_km:.1f}"
    from matplotlib.font_manager import FontProperties
    dist_fp = FontProperties(
        family=["Impact", "Montserrat", "sans-serif"],
        weight="heavy",
        size=88,
    )

    fig.text(
        0.50, 0.345,
        num_str,
        color="#FFFFFF",
        ha="right", va="center",
        fontproperties=dist_fp,
    )
    fig.text(
        0.52, 0.328,
        "KM",
        color=_ORANGE,
        ha="left", va="center",
        fontproperties=font_props("medium", 24),
    )


# ─── Pace + Time row ────────────────────────────────────────────────────────

def _draw_pace_time_row(fig, summary: ActivitySummary) -> None:
    row_y_label = 0.250
    row_y_value = 0.215

    # Align with bottom card centers
    left_cx = 0.2825   # center of elevation card
    right_cx = 0.7175  # center of heart rate card

    # Left: PACE
    fig.text(
        left_cx, row_y_label,
        "PACE",
        color=(1, 1, 1, 0.50),
        ha="center", va="center",
        fontproperties=font_props("bold", 9),
    )
    pace_str = _fmt_pace_colon(summary.avg_pace_min_per_km)
    fig.text(
        left_cx, row_y_value,
        pace_str,
        color="#FFFFFF",
        ha="center", va="center",
        fontproperties=font_props("semibold", 36),
    )
    fig.text(
        left_cx, row_y_value - 0.032,
        "MIN/KM",
        color=(1, 1, 1, 0.40),
        ha="center", va="center",
        fontproperties=font_props("regular", 8),
    )

    # Right: TIME
    fig.text(
        right_cx, row_y_label,
        "TIME",
        color=(1, 1, 1, 0.50),
        ha="center", va="center",
        fontproperties=font_props("bold", 9),
    )
    fig.text(
        right_cx, row_y_value,
        _fmt_hhmmss(summary.moving_time_s),
        color="#FFFFFF",
        ha="center", va="center",
        fontproperties=font_props("semibold", 36),
    )


# ─── Bottom data cards ──────────────────────────────────────────────────────

def _draw_bottom_cards(fig, summary: ActivitySummary) -> None:
    card_y = 0.065
    card_h = 0.100
    gap = 0.03
    card_w = (0.84 - gap) / 2
    left_x = 0.08
    right_x = left_x + card_w + gap

    card_ax = fig.add_axes([0, 0, 1, 1])
    card_ax.axis("off")
    card_ax.patch.set_alpha(0.0)

    surf_rgba = (*_hex_to_rgb(_SURFACE_HIGH), 0.55)

    # ── Left card: ELEVATION ──
    card_ax.add_patch(mpatches.FancyBboxPatch(
        (left_x, card_y), card_w, card_h,
        boxstyle="round,pad=0.006,rounding_size=0.018",
        facecolor=surf_rgba,
        edgecolor=_GHOST_BORDER,
        linewidth=0.7,
        transform=card_ax.transAxes,
    ))

    left_cx = left_x + card_w / 2
    fig.text(
        left_cx, card_y + card_h * 0.78,
        "ELEVATION",
        color=(1, 1, 1, 0.50),
        ha="center", va="center",
        fontproperties=font_props("bold", 8),
    )

    # Icon, value, unit — all centered as a group to handle 1-4 digit values
    draw_icon_shape(fig, left_cx - 0.085, card_y + card_h * 0.35,
                    "mountain", _ORANGE, size=0.014)
    elev_str = f"{int(summary.elevation_gain_m)}" if summary.elevation_gain_m is not None else "—"
    fig.text(
        left_cx, card_y + card_h * 0.35,
        elev_str,
        color="#FFFFFF",
        ha="center", va="center",
        fontproperties=font_props("bold", 24),
    )
    if summary.elevation_gain_m is not None:
        fig.text(
            left_cx, card_y + card_h * 0.10,
            "M",
            color=(1, 1, 1, 0.45),
            ha="center", va="center",
            fontproperties=font_props("bold", 9),
        )

    # ── Right card: AVG HEART RATE ──
    card_ax.add_patch(mpatches.FancyBboxPatch(
        (right_x, card_y), card_w, card_h,
        boxstyle="round,pad=0.006,rounding_size=0.018",
        facecolor=surf_rgba,
        edgecolor=_GHOST_BORDER,
        linewidth=0.7,
        transform=card_ax.transAxes,
    ))

    right_cx = right_x + card_w / 2
    fig.text(
        right_cx, card_y + card_h * 0.78,
        "AVG HEART RATE",
        color=(1, 1, 1, 0.50),
        ha="center", va="center",
        fontproperties=font_props("bold", 8),
    )

    # Unicode heart symbol instead of drawn icon — cleaner at small sizes
    fig.text(
        right_cx - 0.085, card_y + card_h * 0.35,
        "\u2764",
        color="#FF4444",
        ha="center", va="center",
        fontproperties=font_props("regular", 16),
    )
    hr_str = f"{summary.avg_heart_rate_bpm}" if summary.avg_heart_rate_bpm is not None else "—"
    fig.text(
        right_cx, card_y + card_h * 0.35,
        hr_str,
        color="#FFFFFF",
        ha="center", va="center",
        fontproperties=font_props("bold", 24),
    )
    if summary.avg_heart_rate_bpm is not None:
        fig.text(
            right_cx, card_y + card_h * 0.10,
            "BPM",
            color=(1, 1, 1, 0.45),
            ha="center", va="center",
            fontproperties=font_props("bold", 9),
        )
