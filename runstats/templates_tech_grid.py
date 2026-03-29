from __future__ import annotations

import datetime
from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe
import numpy as np

from .models import ActivityData, ActivitySummary
from .template_support import (
    font_props,
    make_figure,
    save_figure,
)
from .templates import TemplateStyle, _hex_to_rgb

_PRIMARY = "#f3ffca"
_PRIMARY_DIM = "#beee00"
_SECONDARY = "#ff734a"
_SURFACE = "#0e0e0e"
_GLASS_BG = (14 / 255, 14 / 255, 14 / 255, 0.4)
_GLASS_BORDER = (1.0, 1.0, 1.0, 0.1)


def _fmt_pace_colon(min_per_km: float) -> str:
    total_s = int(round(min_per_km * 60))
    m, s = divmod(total_s, 60)
    return f"{m:02d}:{s:02d}"


def _fmt_time_compact(seconds: float) -> str:
    total_s = int(round(seconds))
    h, rem = divmod(total_s, 3600)
    m, s = divmod(rem, 60)
    if h > 0:
        return f"{h:02d}:{m:02d}:{s:02d}"
    return f"{m:02d}:{s:02d}"


def _fmt_date_long(activity: ActivityData) -> str:
    for point in activity.points:
        if point.timestamp is not None:
            d = point.timestamp
            return f"{d.strftime('%Y-%m-%d')}"
    return datetime.date.today().strftime("%Y-%m-%d")


def render_tech_grid_overlay(
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
        route_color=_PRIMARY,
        accent_color=_SECONDARY,
    )
    fig = make_figure(style)

    # Base overlay and tech grid
    _draw_dark_base(fig)
    _draw_tech_grid(fig)

    # Header
    _draw_header(fig, location)

    # Route
    if activity.point_count >= 2:
        route_ax = fig.add_axes([0.1, 0.45, 0.8, 0.35])
        _render_route(route_ax, activity)
        fig.text(
            0.5, 0.42,
            "LIVE GPS TRACKING",
            color=(1, 1, 1, 0.3), ha="center", va="center",
            fontproperties=font_props("bold", 10),
        )

    # Bottom cards
    if summary is not None:
        _draw_hero_card(fig, summary)
        _draw_secondary_cards(fig, summary)

    # Bottom nav stub
    _draw_bottom_nav(fig)

    save_figure(fig, output_path, style)


def _draw_dark_base(fig) -> None:
    base_arr = np.zeros((2, 2, 4))
    base_arr[:, :, 3] = 0.40
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(base_arr, aspect="auto", extent=[0, 1, 0, 1], origin="upper")
    ax.axis("off")


def _draw_tech_grid(fig) -> None:
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_xlim(0, 1080)
    ax.set_ylim(0, 1920)
    ax.axis("off")
    # Draw vertical and horizontal lines every 40px
    # to emulate the tech-grid-bg in css
    for x in range(0, 1080, 40):
        ax.axvline(x, color="white", alpha=0.05, linewidth=1)
    for y in range(0, 1920, 40):
        ax.axhline(y, color="white", alpha=0.05, linewidth=1)


def _draw_header(fig, location: str | None) -> None:
    loc_str = (location or "AMSTERDAM, NL").upper()
    fig.text(
        0.5, 0.94,
        loc_str,
        color=_PRIMARY, ha="center", va="center",
        fontproperties=font_props("medium", 16)
    )


def _render_route(ax, activity: ActivityData) -> None:
    lons = activity.longitudes
    lats = activity.latitudes

    (line,) = ax.plot(
        lons, lats,
        color=_PRIMARY,
        linewidth=3.0,
        linestyle=(0, (8, 4)),
        solid_capstyle="round",
        dash_capstyle="round",
        alpha=0.90,
        zorder=3,
    )
    
    # Simulate glow filter: drop-shadow(0 0 8px rgba(243, 255, 202, 0.4))
    r, g, b = _hex_to_rgb(_PRIMARY)
    line.set_path_effects([
        pe.withStroke(linewidth=12, foreground=(r, g, b, 0.2)),
        pe.withStroke(linewidth=7, foreground=(r, g, b, 0.4)),
        pe.Normal(),
    ])

    if lons:
        c1 = mpatches.Circle((lons[0], lats[0]), radius=0.00005, color=_PRIMARY, transform=ax.transData, zorder=4)
        ax.add_patch(c1)
        c2 = mpatches.Circle((lons[-1], lats[-1]), radius=0.00008, color=_PRIMARY, alpha=0.9, transform=ax.transData, zorder=4)
        ax.add_patch(c2)

    lon_min, lon_max = min(lons), max(lons)
    lat_min, lat_max = min(lats), max(lats)
    w = max(lon_max - lon_min, 1e-9)
    h = max(lat_max - lat_min, 1e-9)
    ax.set_xlim(lon_min - w * 0.1, lon_max + w * 0.1)
    ax.set_ylim(lat_min - h * 0.1, lat_max + h * 0.1)
    ax.set_aspect("equal", adjustable="datalim")
    ax.axis("off")


def _add_glass_panel(fig, x0: float, y0: float, width: float, height: float) -> None:
    w, h = fig.get_size_inches()
    aspect = w / h
    rect = mpatches.FancyBboxPatch(
        (x0, y0), width, height,
        boxstyle="round,pad=0.0,rounding_size=0.02",
        mutation_aspect=1/aspect,
        facecolor=_GLASS_BG,
        edgecolor=_GLASS_BORDER,
        linewidth=1.0,
        transform=fig.transFigure,
        zorder=2
    )
    fig.patches.append(rect)


def _draw_hero_card(fig, summary: ActivitySummary) -> None:
    x0, y0, w, h = 0.15, 0.26, 0.70, 0.12
    _add_glass_panel(fig, x0, y0, w, h)

    # Accent side bar (primary)
    bar = mpatches.Rectangle(
        (x0, y0), 0.008, h,
        facecolor=(*_hex_to_rgb(_PRIMARY), 0.3),
        edgecolor="none",
        transform=fig.transFigure,
        zorder=3
    )
    fig.patches.append(bar)

    fig.text(
        0.5, y0 + h * 0.70,
        "TOTAL DISTANCE",
        color=(1, 1, 1, 0.5), ha="center", va="center",
        fontproperties=font_props("bold", 11)
    )

    num_str = f"{summary.distance_km:.2f}"
    # Calculate approx text placements to stick 'KM' next to value
    fig.text(
        0.5 - 0.04, y0 + h * 0.30,
        num_str,
        color=_PRIMARY, ha="right", va="center",
        fontproperties=font_props("heavy", 72)
    )
    fig.text(
        0.51 - 0.04, y0 + h * 0.30,
        "KM",
        color=_PRIMARY_DIM, ha="left", va="center", # _primary-dim is visually similar to secondary scale
        fontproperties=font_props("bold", 20)
    )


def _draw_secondary_cards(fig, summary: ActivitySummary) -> None:
    w, h = 0.34, 0.10
    
    # Pace Card
    x1, y1 = 0.15, 0.14
    _add_glass_panel(fig, x1, y1, w, h)
    
    fig.text(
        x1 + 0.05, y1 + h * 0.70,
        "PACE",
        color=(1, 1, 1, 0.4), ha="left", va="center",
        fontproperties=font_props("bold", 10)
    )
    pace_str = _fmt_pace_colon(summary.avg_pace_min_per_km)
    fig.text(
        x1 + 0.05, y1 + h * 0.30,
        pace_str,
        color="#FFFFFF", ha="left", va="center",
        fontproperties=font_props("medium", 28)
    )
    fig.text(
        x1 + 0.05 + len(pace_str) * 0.024, y1 + h * 0.30,
        "/KM",
        color=(1, 1, 1, 0.3), ha="left", va="center",
        fontproperties=font_props("medium", 12)
    )

    # Time Card
    x2 = 0.51
    _add_glass_panel(fig, x2, y1, w, h)
    fig.text(
        x2 + 0.05, y1 + h * 0.70,
        "TIME",
        color=(1, 1, 1, 0.4), ha="left", va="center",
        fontproperties=font_props("bold", 10)
    )
    time_str = _fmt_time_compact(summary.moving_time_s)
    fig.text(
        x2 + 0.05, y1 + h * 0.30,
        time_str,
        color="#FFFFFF", ha="left", va="center",
        fontproperties=font_props("medium", 28)
    )


def _draw_bottom_nav(fig) -> None:
    # A dark semi-transparent block at the very bottom
    nav_h = 0.075
    rect = mpatches.Rectangle(
        (0, 0), 1, nav_h,
        facecolor=(14/255, 14/255, 14/255, 0.6),
        edgecolor="none",
        transform=fig.transFigure,
        zorder=10
    )
    fig.patches.append(rect)

    fig.text(
        0.5, nav_h * 0.45,
        "ROUTE",
        color=_PRIMARY, ha="center", va="center",
        fontproperties=font_props("bold", 10)
    )
    
    # Simple active indicator
    line = mlines.Line2D(
        [0.46, 0.54], [nav_h * 0.15, nav_h * 0.15],
        color=_PRIMARY, linewidth=3,
        transform=fig.transFigure,
    )
    fig.lines.append(line)
