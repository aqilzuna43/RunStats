from __future__ import annotations

from pathlib import Path

from .metrics import format_distance_km, format_duration, format_pace
from .models import ActivityData, ActivitySummary
from .render import RouteStyle, render_route
from .template_support import (
    add_separator_line,
    add_stat_row,
    font_props,
    make_figure,
    save_figure,
)
from .templates import TemplateStyle


def render_story_overlay(
    activity: ActivityData,
    output_path: str | Path,
    route_mode: str,
    summary: ActivitySummary | None,
    title: str | None,
) -> None:
    style = TemplateStyle(canvas_width_px=1080, canvas_height_px=1920, dpi=200)
    fig = make_figure(style)
    has_route = activity.point_count >= 2

    if summary is not None and has_route:
        route_ax = fig.add_axes([0.08, 0.50, 0.84, 0.44])
        render_route(route_ax, activity, RouteStyle(mode=route_mode, line_width=4.5))
        add_separator_line(fig, 0.47, 0.25, 0.75, style)
        add_stat_row(fig, "Distance", format_distance_km(summary.distance_km), 0.38, style)
        add_stat_row(fig, "Pace", format_pace(summary.avg_pace_min_per_km), 0.27, style)
        add_stat_row(fig, "Time", format_duration(summary.moving_time_s), 0.16, style)
    elif summary is not None:
        add_stat_row(fig, "Distance", format_distance_km(summary.distance_km), 0.65, style)
        add_stat_row(fig, "Pace", format_pace(summary.avg_pace_min_per_km), 0.48, style)
        add_stat_row(fig, "Time", format_duration(summary.moving_time_s), 0.31, style)
    else:
        route_ax = fig.add_axes([0.08, 0.20, 0.84, 0.72])
        render_route(route_ax, activity, RouteStyle(mode=route_mode, line_width=4.5))

    save_figure(fig, output_path, style)


def render_clean_card(
    activity: ActivityData,
    output_path: str | Path,
    route_mode: str,
    summary: ActivitySummary | None,
    title: str | None,
) -> None:
    from matplotlib.patches import FancyBboxPatch

    style = TemplateStyle(
        canvas_width_px=1600,
        canvas_height_px=1600,
        dpi=200,
        panel_color="#151515",
        panel_alpha=0.88,
    )
    fig = make_figure(style)
    has_route = activity.point_count >= 2

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
            fontsize=36,
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

    save_figure(fig, output_path, style)
