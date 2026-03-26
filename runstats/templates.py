from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.patches import FancyBboxPatch

from .metrics import format_distance_km, format_duration, format_pace
from .models import ActivityData, ActivitySummary
from .render import RouteStyle, render_route


DEFAULT_TITLE = "RELENTLESS"
TEMPLATE_NAMES = ("story_overlay", "clean_card")


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
) -> None:
    if template_name == "story_overlay":
        _render_story_overlay(activity, output_path, route_mode, summary, title)
        return
    if template_name == "clean_card":
        _render_clean_card(activity, output_path, route_mode, summary, title)
        return

    raise ValueError(f"Unknown template: {template_name}")


def _render_story_overlay(
    activity: ActivityData,
    output_path: str | Path,
    route_mode: str,
    summary: ActivitySummary | None,
    title: str | None,
) -> None:
    style = TemplateStyle(canvas_width_px=1080, canvas_height_px=1920, dpi=200)
    fig = _make_figure(style)
    has_route = len(activity.points) >= 2

    if summary is not None and has_route:
        route_ax = fig.add_axes([0.08, 0.50, 0.84, 0.44])
        render_route(route_ax, activity, RouteStyle(mode=route_mode, line_width=4.5))
        _add_separator_line(fig, 0.47, 0.25, 0.75, style)
        _add_stat_row(fig, "Distance", format_distance_km(summary.distance_km), 0.38, style)
        _add_stat_row(fig, "Pace", format_pace(summary.avg_pace_min_per_km), 0.27, style)
        _add_stat_row(fig, "Time", format_duration(summary.moving_time_s), 0.16, style)
    elif summary is not None:
        _add_stat_row(fig, "Distance", format_distance_km(summary.distance_km), 0.65, style)
        _add_stat_row(fig, "Pace", format_pace(summary.avg_pace_min_per_km), 0.48, style)
        _add_stat_row(fig, "Time", format_duration(summary.moving_time_s), 0.31, style)
    else:
        route_ax = fig.add_axes([0.08, 0.20, 0.84, 0.72])
        render_route(route_ax, activity, RouteStyle(mode=route_mode, line_width=4.5))

    _save_figure(fig, output_path, style)


def _render_clean_card(
    activity: ActivityData,
    output_path: str | Path,
    route_mode: str,
    summary: ActivitySummary | None,
    title: str | None,
) -> None:
    style = TemplateStyle(
        canvas_width_px=1600,
        canvas_height_px=1600,
        dpi=200,
        panel_color="#151515",
        panel_alpha=0.88,
    )
    fig = _make_figure(style)
    has_route = len(activity.points) >= 2

    panel_ax = fig.add_axes([0, 0, 1, 1])
    panel_ax.axis("off")
    panel_ax.patch.set_alpha(0.0)
    panel = FancyBboxPatch(
        (0.08, 0.08),
        0.84,
        0.84,
        boxstyle="round,pad=0.02,rounding_size=0.06",
        facecolor=style.panel_color,
        edgecolor=(1, 1, 1, 0.08),
        linewidth=2,
        alpha=style.panel_alpha,
        transform=panel_ax.transAxes,
    )
    panel_ax.add_patch(panel)

    if title:
        fig.text(
            0.5,
            0.84,
            title,
            color=style.title_color,
            ha="center",
            va="center",
            fontsize=32,
            weight="bold",
        )

    if has_route:
        route_ax = fig.add_axes([0.18, 0.38, 0.64, 0.34])
        render_route(route_ax, activity, RouteStyle(mode=route_mode, line_width=8.0))

    if summary is not None:
        baseline_y = 0.20 if has_route else 0.42
        stats = [
            ("Distance", format_distance_km(summary.distance_km), 0.20),
            ("Pace", format_pace(summary.avg_pace_min_per_km), 0.50),
            ("Time", format_duration(summary.moving_time_s), 0.80),
        ]
        for label, value, xpos in stats:
            fig.text(
                xpos,
                baseline_y + 0.05,
                label,
                color=style.text_color,
                ha="center",
                va="center",
                fontsize=20,
                alpha=0.8,
                weight="bold",
            )
            fig.text(
                xpos,
                baseline_y,
                value,
                color=style.text_color,
                ha="center",
                va="center",
                fontsize=24,
                weight="heavy",
            )

    _save_figure(fig, output_path, style)


def _make_figure(style: TemplateStyle) -> plt.Figure:
    figure = plt.figure(
        figsize=(style.canvas_width_px / style.dpi, style.canvas_height_px / style.dpi),
        dpi=style.dpi,
        facecolor=(0, 0, 0, 0),
    )
    figure.patch.set_alpha(0.0)
    return figure


def _font_props(weight: str, size: int) -> FontProperties:
    return FontProperties(family="Montserrat", weight=weight, size=size)


def _add_stat_row(
    fig: plt.Figure,
    label: str,
    value: str,
    y: float,
    style: TemplateStyle,
) -> None:
    fig.text(
        0.5,
        y + 0.04,
        label,
        color=style.text_color,
        ha="center",
        va="center",
        fontproperties=_font_props("bold", 22),
        alpha=0.65,
    )
    fig.text(
        0.5,
        y - 0.02,
        value,
        color=style.text_color,
        ha="center",
        va="center",
        fontproperties=_font_props("heavy", 42),
    )


def _add_separator_line(
    fig: plt.Figure,
    y: float,
    x_start: float,
    x_end: float,
    style: TemplateStyle,
) -> None:
    line = mlines.Line2D(
        [x_start, x_end],
        [y, y],
        transform=fig.transFigure,
        color=style.accent_color,
        linewidth=2.5,
        alpha=style.accent_alpha,
    )
    fig.lines.append(line)


def _save_figure(fig: plt.Figure, output_path: str | Path, style: TemplateStyle) -> None:
    fig.savefig(
        output_path,
        dpi=style.dpi,
        transparent=True,
        bbox_inches=None,
        pad_inches=0,
    )
    plt.close(fig)
