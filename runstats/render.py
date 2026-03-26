from __future__ import annotations

from dataclasses import dataclass

import matplotlib.colors as mcolors
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.collections import LineCollection

from .models import ActivityData


SAFETY_ORANGE = "#FF5500"
SPEED_CMAP = mcolors.LinearSegmentedColormap.from_list(
    "garmin_speed",
    ["#0000FF", "#00BFFF", "#00FF00", "#FFFF00", "#FF8000", "#FF0000"],
)


@dataclass(frozen=True)
class RouteStyle:
    mode: str = "solid"
    color: str = SAFETY_ORANGE
    line_width: float = 6.0


def render_route(ax: plt.Axes, activity: ActivityData, style: RouteStyle) -> None:
    lons = np.array(activity.longitudes, dtype=float)
    lats = np.array(activity.latitudes, dtype=float)

    if len(lons) < 2 or len(lats) < 2:
        raise ValueError("At least two route points are required to render the route.")

    if style.mode == "gradient" and activity.has_speed_data():
        speeds = np.array(activity.speeds_mps, dtype=float)
        _render_gradient(ax, lons, lats, speeds, style.line_width)
    else:
        _render_solid(ax, lons, lats, style)

    _apply_limits(ax, lons, lats)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.patch.set_alpha(0.0)


def _render_solid(ax: plt.Axes, lons: np.ndarray, lats: np.ndarray, style: RouteStyle) -> None:
    ax.plot(
        lons,
        lats,
        color=style.color,
        linewidth=style.line_width,
        solid_capstyle="round",
        solid_joinstyle="round",
    )


def _render_gradient(
    ax: plt.Axes, lons: np.ndarray, lats: np.ndarray, speeds: np.ndarray, line_width: float
) -> None:
    points = np.column_stack([lons, lats]).reshape(-1, 1, 2)
    segments = np.concatenate([points[:-1], points[1:]], axis=1)
    seg_speeds = (speeds[:-1] + speeds[1:]) / 2.0

    nonzero = speeds[speeds > 0.1]
    if len(nonzero) > 0:
        vmin = float(np.percentile(nonzero, 5))
        vmax = float(np.percentile(nonzero, 95))
        if vmin == vmax:
            vmax = vmin + 0.1
    else:
        vmin, vmax = 0.0, 1.0

    norm = mcolors.Normalize(vmin=vmin, vmax=vmax)
    line_collection = LineCollection(
        segments,
        cmap=SPEED_CMAP,
        norm=norm,
        capstyle="round",
        joinstyle="round",
    )
    line_collection.set_array(seg_speeds)
    line_collection.set_linewidth(line_width)
    ax.add_collection(line_collection)


def _apply_limits(ax: plt.Axes, lons: np.ndarray, lats: np.ndarray, padding_ratio: float = 0.08) -> None:
    lon_min, lon_max = float(lons.min()), float(lons.max())
    lat_min, lat_max = float(lats.min()), float(lats.max())

    width = max(lon_max - lon_min, 1e-9)
    height = max(lat_max - lat_min, 1e-9)
    padding_x = width * padding_ratio
    padding_y = height * padding_ratio

    ax.set_xlim(lon_min - padding_x, lon_max + padding_x)
    ax.set_ylim(lat_min - padding_y, lat_max + padding_y)
