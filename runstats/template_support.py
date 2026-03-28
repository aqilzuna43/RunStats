from __future__ import annotations

import datetime
from functools import lru_cache
from pathlib import Path
from typing import Any

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
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
