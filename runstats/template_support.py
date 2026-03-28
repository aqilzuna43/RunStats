from __future__ import annotations

import datetime
import math
from functools import lru_cache
from pathlib import Path
from typing import Any

import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.path as mpath
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.font_manager import FontProperties

from .models import ActivityData

FONT_FAMILIES = ["Montserrat", "DejaVu Sans", "sans-serif"]


def fmt_optional(value: int | None, suffix: str, fallback: str = "N/A") -> str:
    return f"{value}{suffix}" if value is not None else fallback


def activity_date_str(activity: ActivityData) -> str:
    for point in activity.points:
        if point.timestamp is not None:
            date_value = point.timestamp
            return f"{date_value.day} {date_value.strftime('%b %Y').upper()}"
    today = datetime.date.today()
    return f"{today.day} {today.strftime('%b %Y').upper()}"


def fmt_pace_apos(min_per_km: float) -> str:
    total_seconds = int(round(min_per_km * 60))
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}'{seconds:02d}\""


def fmt_duration_colon(seconds: float) -> str:
    rounded = int(round(seconds))
    hours, remainder = divmod(rounded, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{secs:02d}"
    return f"{minutes:02d}:{secs:02d}"


def make_figure(style: Any) -> plt.Figure:
    figure = plt.figure(
        figsize=(style.canvas_width_px / style.dpi, style.canvas_height_px / style.dpi),
        dpi=style.dpi,
        facecolor=(0, 0, 0, 0),
    )
    figure.patch.set_alpha(0.0)
    return figure


@lru_cache(maxsize=None)
def font_props(weight: str, size: int) -> FontProperties:
    return FontProperties(family=FONT_FAMILIES, weight=weight, size=size)


def add_stat_row(fig: plt.Figure, label: str, value: str, y: float, style: Any) -> None:
    fig.text(
        0.5,
        y + 0.04,
        label,
        color=style.text_color,
        ha="center",
        va="center",
        fontproperties=font_props("bold", 22),
        alpha=0.65,
    )
    fig.text(
        0.5,
        y - 0.02,
        value,
        color=style.text_color,
        ha="center",
        va="center",
        fontproperties=font_props("heavy", 42),
    )


def add_separator_line(fig: plt.Figure, y: float, x_start: float, x_end: float, style: Any) -> None:
    line = mlines.Line2D(
        [x_start, x_end],
        [y, y],
        transform=fig.transFigure,
        color=style.accent_color,
        linewidth=2.5,
        alpha=style.accent_alpha,
    )
    fig.lines.append(line)


def save_figure(fig: plt.Figure, output_path: str | Path, style: Any) -> None:
    fig.savefig(
        output_path,
        dpi=style.dpi,
        transparent=True,
        bbox_inches=None,
        pad_inches=0,
    )
    plt.close(fig)


# ─────────────────────────────────────────────
# New helpers for sleek template rendering
# ─────────────────────────────────────────────


def draw_route_markers(
    ax: plt.Axes,
    activity: ActivityData,
    start_color: str,
    end_color: str,
    marker_size: float = 8,
) -> None:
    lons = activity.longitudes
    lats = activity.latitudes
    if len(lons) < 2:
        return
    ax.plot(lons[0], lats[0], "o", color=start_color,
            markersize=marker_size, zorder=10, markeredgewidth=0)
    ax.plot(lons[-1], lats[-1], "o", color=end_color,
            markersize=marker_size, zorder=10, markeredgewidth=0)


def draw_grid_overlay(
    ax: plt.Axes,
    num_lines: int = 15,
    color_rgba: tuple[float, float, float, float] = (1, 1, 1, 0.03),
) -> None:
    x_min, x_max = ax.get_xlim()
    y_min, y_max = ax.get_ylim()
    x_step = (x_max - x_min) / num_lines
    y_step = (y_max - y_min) / num_lines
    for i in range(1, num_lines):
        ax.axhline(y_min + i * y_step, color=color_rgba[:3],
                   alpha=color_rgba[3], linewidth=0.5, zorder=1)
        ax.axvline(x_min + i * x_step, color=color_rgba[:3],
                   alpha=color_rgba[3], linewidth=0.5, zorder=1)


def radial_glow_image(
    W: int,
    H: int,
    cx_frac: float,
    cy_frac: float,
    radius_frac: float,
    color_hex: str,
    peak_alpha: float,
) -> np.ndarray:
    from .templates import _hex_to_rgb

    r, g, b = _hex_to_rgb(color_hex)
    xx = np.linspace(0, 1, W)
    yy = np.linspace(0, 1, H)
    XX, YY = np.meshgrid(xx, yy)
    dist = np.sqrt((XX - cx_frac) ** 2 + (YY - cy_frac) ** 2)
    sigma = radius_frac / 2.0
    alpha = peak_alpha * np.exp(-dist ** 2 / (2 * sigma ** 2))
    rgba = np.zeros((H, W, 4), dtype=float)
    rgba[:, :, 0] = r
    rgba[:, :, 1] = g
    rgba[:, :, 2] = b
    rgba[:, :, 3] = alpha
    return rgba


def gradient_fade_line(
    fig: plt.Figure,
    y: float,
    x_start: float,
    x_end: float,
    color_hex: str,
    peak_alpha: float = 0.20,
) -> None:
    from .templates import _hex_to_rgb

    r, g, b = _hex_to_rgb(color_hex)
    width = 256
    alpha_ramp = np.zeros(width)
    for i in range(width):
        t = i / (width - 1)
        alpha_ramp[i] = peak_alpha * math.sin(t * math.pi)

    img = np.zeros((1, width, 4))
    img[0, :, 0] = r
    img[0, :, 1] = g
    img[0, :, 2] = b
    img[0, :, 3] = alpha_ramp

    line_height = 0.003
    line_ax = fig.add_axes([x_start, y - line_height / 2, x_end - x_start, line_height])
    line_ax.imshow(img, aspect="auto", extent=[0, 1, 0, 1], origin="upper")
    line_ax.axis("off")


def draw_icon_shape(
    fig: plt.Figure,
    x: float,
    y: float,
    icon_type: str,
    color: str,
    size: float = 0.018,
) -> None:
    """Draw a geometric icon shape at figure coordinates (x, y)."""
    if icon_type == "arrow_up_right":
        _draw_arrow_up_right(fig, x, y, color, size)
    elif icon_type == "clock":
        _draw_clock(fig, x, y, color, size)
    elif icon_type == "target":
        _draw_target(fig, x, y, color, size)
    elif icon_type == "heart":
        _draw_heart(fig, x, y, color, size)
    elif icon_type == "mountain":
        _draw_mountain(fig, x, y, color, size)


def _draw_arrow_up_right(fig: plt.Figure, x: float, y: float, color: str, s: float) -> None:
    # Diagonal arrow: line from bottom-left to top-right with arrowhead
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.patch.set_alpha(0.0)
    arrow = mpatches.FancyArrowPatch(
        (x - s * 0.5, y - s * 0.5),
        (x + s * 0.5, y + s * 0.5),
        arrowstyle="->,head_length=4,head_width=3",
        color=color,
        linewidth=2.0,
        transform=fig.transFigure,
        mutation_scale=1,
    )
    ax.add_patch(arrow)


def _draw_clock(fig: plt.Figure, x: float, y: float, color: str, s: float) -> None:
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.patch.set_alpha(0.0)
    # Circle outline
    circle = mpatches.Circle(
        (x, y), s * 0.55,
        facecolor="none", edgecolor=color, linewidth=1.8,
        transform=fig.transFigure,
    )
    ax.add_patch(circle)
    # Hour hand (pointing up-right)
    fig.lines.append(mlines.Line2D(
        [x, x], [y, y + s * 0.35],
        transform=fig.transFigure, color=color, linewidth=1.8,
        solid_capstyle="round",
    ))
    # Minute hand (pointing right)
    fig.lines.append(mlines.Line2D(
        [x, x + s * 0.30], [y, y],
        transform=fig.transFigure, color=color, linewidth=1.8,
        solid_capstyle="round",
    ))


def _draw_target(fig: plt.Figure, x: float, y: float, color: str, s: float) -> None:
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.patch.set_alpha(0.0)
    # Outer circle
    ax.add_patch(mpatches.Circle(
        (x, y), s * 0.55, facecolor="none", edgecolor=color,
        linewidth=1.5, transform=fig.transFigure,
    ))
    # Inner circle
    ax.add_patch(mpatches.Circle(
        (x, y), s * 0.30, facecolor="none", edgecolor=color,
        linewidth=1.5, transform=fig.transFigure,
    ))
    # Center dot
    ax.add_patch(mpatches.Circle(
        (x, y), s * 0.08, facecolor=color, edgecolor="none",
        transform=fig.transFigure,
    ))


def _draw_heart(fig: plt.Figure, x: float, y: float, color: str, s: float) -> None:
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.patch.set_alpha(0.0)

    # Heart shape using bezier curves
    hs = s * 0.6
    verts = [
        (x, y - hs * 0.4),                            # bottom point
        (x - hs * 0.55, y + hs * 0.1),                # left curve control 1
        (x - hs * 0.55, y + hs * 0.65),               # left curve control 2
        (x, y + hs * 0.35),                            # top center dip
        (x + hs * 0.55, y + hs * 0.65),               # right curve control 1
        (x + hs * 0.55, y + hs * 0.1),                # right curve control 2
        (x, y - hs * 0.4),                            # back to bottom
    ]
    codes = [
        mpath.Path.MOVETO,
        mpath.Path.CURVE3,
        mpath.Path.CURVE3,
        mpath.Path.CURVE3,
        mpath.Path.CURVE3,
        mpath.Path.CURVE3,
        mpath.Path.CURVE3,
    ]
    path = mpath.Path(verts, codes)
    patch = mpatches.PathPatch(
        path, facecolor=color, edgecolor="none",
        transform=fig.transFigure,
    )
    ax.add_patch(patch)


def _draw_mountain(fig: plt.Figure, x: float, y: float, color: str, s: float) -> None:
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.patch.set_alpha(0.0)

    # Mountain: two overlapping triangles (main peak + smaller peak)
    # Main peak
    main_verts = [
        (x - s * 0.55, y - s * 0.35),
        (x + s * 0.05, y + s * 0.45),
        (x + s * 0.55, y - s * 0.35),
    ]
    main_tri = mpatches.Polygon(
        main_verts, closed=True,
        facecolor=color, edgecolor="none",
        transform=fig.transFigure,
    )
    ax.add_patch(main_tri)

    # Smaller peak (offset right, slightly behind)
    small_verts = [
        (x + s * 0.05, y - s * 0.35),
        (x + s * 0.35, y + s * 0.15),
        (x + s * 0.55, y - s * 0.35),
    ]
    small_tri = mpatches.Polygon(
        small_verts, closed=True,
        facecolor=color, edgecolor="none", alpha=0.5,
        transform=fig.transFigure,
    )
    ax.add_patch(small_tri)
