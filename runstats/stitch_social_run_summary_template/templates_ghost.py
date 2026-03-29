from __future__ import annotations

from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import numpy as np

from .models import ActivityData, ActivitySummary
from .template_support import (
    draw_route_markers,
    fmt_duration_colon,
    fmt_pace_apos,
    font_props,
    make_figure,
    save_figure,
)
from .templates import TemplateStyle

_CORAL = "#ff734a"
_LIME = "#f3ffca"


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

    # ── Background vignette ────────────────────────────────────────────
    _draw_vignette(fig, W, H)

    # ── Location header ────────────────────────────────────────────────
    if location:
        fig.text(
            0.5, 0.955,
            location.upper(),
            color=(1, 1, 1, 0.75),
            ha="center", va="center",
            fontproperties=font_props("bold", 17),
        )

    # ── GPS route ──────────────────────────────────────────────────────
    if activity.point_count >= 2:
        route_ax = fig.add_axes([0.15, 0.38, 0.70, 0.43])
        _render_glowing_route(route_ax, activity)
        draw_route_markers(route_ax, activity, _CORAL, _LIME, marker_size=8)

    # ── Hero distance ──────────────────────────────────────────────────
    if summary is not None:
        fig.text(
            0.5, 0.352,
            "DISTANCE",
            color=(1, 1, 1, 0.40),
            ha="center", va="center",
            fontproperties=font_props("bold", 13),
        )

        num_str = f"{summary.distance_km:.2f}"
        fig.text(
            0.5, 0.285,
            num_str,
            color="#FFFFFF",
            ha="center", va="center",
            fontproperties=font_props("heavy", 78),
        )
        # KM suffix — estimate right edge of centered number
        km_x = 0.5 + len(num_str) * 0.031 + 0.012
        fig.text(
            km_x, 0.268,
            "KM",
            color=_LIME,
            ha="left", va="center",
            fontproperties=font_props("semibold", 22),
        )

        # ── Frosted glass card ─────────────────────────────────────────
        _draw_glass_card(fig, summary)

    save_figure(fig, output_path, style)


def _draw_vignette(fig, W: int, H: int) -> None:
    """Dark gradient bands at top and bottom of the canvas."""
    # Top band: opaque at edge, fades to transparent downward
    top_alpha = np.linspace(0.60, 0.0, 256)
    top_rgba = np.zeros((256, 1, 4))
    top_rgba[:, 0, 3] = top_alpha
    top_ax = fig.add_axes([0, 0.83, 1, 0.17])
    top_ax.imshow(top_rgba, aspect="auto", extent=[0, 1, 0, 1], origin="upper")
    top_ax.axis("off")

    # Bottom band: transparent at top, fades to dark at edge
    bot_alpha = np.linspace(0.0, 0.80, 256)
    bot_rgba = np.zeros((256, 1, 4))
    bot_rgba[:, 0, 3] = bot_alpha
    bot_ax = fig.add_axes([0, 0, 1, 0.29])
    bot_ax.imshow(bot_rgba, aspect="auto", extent=[0, 1, 0, 1], origin="lower")
    bot_ax.axis("off")


def _render_glowing_route(ax, activity: ActivityData) -> None:
    """Dashed coral route line with a soft radial glow."""
    lons = activity.longitudes
    lats = activity.latitudes

    (line,) = ax.plot(
        lons, lats,
        color=_CORAL,
        linewidth=3.5,
        linestyle=(0, (7, 7)),
        dash_capstyle="round",
        solid_joinstyle="round",
        alpha=0.90,
        zorder=3,
    )
    line.set_path_effects([
        pe.withStroke(linewidth=12, foreground=(1.0, 0.451, 0.290, 0.18)),
        pe.withStroke(linewidth=7,  foreground=(1.0, 0.451, 0.290, 0.32)),
        pe.Normal(),
    ])

    lon_min, lon_max = min(lons), max(lons)
    lat_min, lat_max = min(lats), max(lats)
    w = max(lon_max - lon_min, 1e-9)
    h = max(lat_max - lat_min, 1e-9)
    ax.set_xlim(lon_min - w * 0.05, lon_max + w * 0.05)
    ax.set_ylim(lat_min - h * 0.05, lat_max + h * 0.05)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.patch.set_alpha(0.0)


def _draw_glass_card(fig, summary: ActivitySummary) -> None:
    """Two-column frosted glass card: AVG PACE | TIME."""
    card_x, card_y = 0.065, 0.068
    card_w, card_h = 0.870, 0.148

    glass_ax = fig.add_axes([0, 0, 1, 1])
    glass_ax.axis("off")
    glass_ax.patch.set_alpha(0.0)

    # Outer halo for perceived depth
    glass_ax.add_patch(mpatches.FancyBboxPatch(
        (card_x - 0.004, card_y - 0.003), card_w + 0.008, card_h + 0.006,
        boxstyle="round,pad=0.01,rounding_size=0.03",
        facecolor="none",
        edgecolor=(1, 1, 1, 0.05),
        linewidth=3,
        transform=glass_ax.transAxes,
    ))

    # Main glass surface
    glass_ax.add_patch(mpatches.FancyBboxPatch(
        (card_x, card_y), card_w, card_h,
        boxstyle="round,pad=0.01,rounding_size=0.03",
        facecolor=(1, 1, 1, 0.08),
        edgecolor=(1, 1, 1, 0.10),
        linewidth=1.2,
        transform=glass_ax.transAxes,
    ))

    # Vertical column divider
    fig.lines.append(mlines.Line2D(
        [0.5, 0.5],
        [card_y + 0.022, card_y + card_h - 0.022],
        transform=fig.transFigure,
        color=(1, 1, 1, 0.12),
        linewidth=1.0,
    ))

    label_y = card_y + card_h * 0.72
    value_y = card_y + card_h * 0.30

    # Left column: AVG PACE (label in coral per the Stitch design)
    fig.text(
        0.275, label_y, "AVG PACE",
        color=_CORAL,
        ha="center", va="center",
        fontproperties=font_props("bold", 11),
    )
    fig.text(
        0.275, value_y,
        fmt_pace_apos(summary.avg_pace_min_per_km) + " /km",
        color="#FFFFFF",
        ha="center", va="center",
        fontproperties=font_props("semibold", 24),
    )

    # Right column: TIME (label in muted white)
    fig.text(
        0.725, label_y, "TIME",
        color=(1, 1, 1, 0.45),
        ha="center", va="center",
        fontproperties=font_props("bold", 11),
    )
    fig.text(
        0.725, value_y,
        fmt_duration_colon(summary.moving_time_s),
        color="#FFFFFF",
        ha="center", va="center",
        fontproperties=font_props("semibold", 24),
    )
