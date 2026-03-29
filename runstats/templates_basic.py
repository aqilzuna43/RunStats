from __future__ import annotations

from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.patheffects as pe

from .metrics import format_distance_km, format_duration, format_pace
from .models import ActivityData, ActivitySummary
from .render import RouteStyle, render_route
from .template_support import (
    draw_route_markers,
    fmt_duration_colon,
    fmt_pace_apos,
    font_props,
    make_figure,
    save_figure,
)
from .templates import TemplateStyle


# Shared path effect: dark stroke so white text reads over any photo background.
_STROKE = [pe.withStroke(linewidth=4, foreground=(0, 0, 0, 0.55))]
_STROKE_LIGHT = [pe.withStroke(linewidth=2, foreground=(0, 0, 0, 0.45))]


def render_story_overlay(
    activity: ActivityData,
    output_path: str | Path,
    route_mode: str,
    summary: ActivitySummary | None,
    title: str | None,
    location: str | None = None,
) -> None:
    style = TemplateStyle(canvas_width_px=1080, canvas_height_px=1920, dpi=200)
    fig = make_figure(style)
    has_route = activity.point_count >= 2

    # Route sits as a centered hero panel, closer to the glass proportions.
    if has_route:
        route_ax = fig.add_axes([0.15, 0.40, 0.70, 0.41])
        render_route(route_ax, activity, RouteStyle(mode=route_mode, line_width=5.0))
        draw_route_markers(route_ax, activity, "#4ade80", "#f97316", marker_size=8)

    if location:
        fig.text(
            0.5,
            0.955,
            location,
            color=(1, 1, 1, 0.82),
            ha="center",
            va="center",
            fontproperties=font_props("bold", 20),
            path_effects=_STROKE_LIGHT,
        )

    if summary is not None:
        fig.lines.append(
            mlines.Line2D(
                [0.28, 0.72],
                [0.338, 0.338],
                transform=fig.transFigure,
                color=style.accent_color,
                linewidth=2.5,
                solid_capstyle="round",
            )
        )

        num_str = f"{summary.distance_km:.2f}"
        fig.text(
            0.5,
            0.255,
            num_str,
            color="#FFFFFF",
            ha="center",
            va="center",
            fontproperties=font_props("heavy", 74),
            path_effects=_STROKE,
        )
        fig.text(
            0.5,
            0.198,
            "km",
            color=(1, 1, 1, 0.60),
            ha="center",
            va="center",
            fontproperties=font_props("bold", 22),
            path_effects=_STROKE_LIGHT,
        )

        pace_str = fmt_pace_apos(summary.avg_pace_min_per_km) + " /km"
        time_str = fmt_duration_colon(summary.moving_time_s)

        fig.text(
            0.28,
            0.148,
            "AVG PACE",
            color=(1, 1, 1, 0.55),
            ha="center",
            va="center",
            fontsize=12,
            weight="bold",
            path_effects=_STROKE_LIGHT,
        )
        fig.text(
            0.28,
            0.112,
            pace_str,
            color="#FFFFFF",
            ha="center",
            va="center",
            fontproperties=font_props("bold", 28),
            path_effects=_STROKE,
        )

        fig.text(
            0.72,
            0.148,
            "TIME",
            color=(1, 1, 1, 0.55),
            ha="center",
            va="center",
            fontsize=12,
            weight="bold",
            path_effects=_STROKE_LIGHT,
        )
        fig.text(
            0.72,
            0.112,
            time_str,
            color="#FFFFFF",
            ha="center",
            va="center",
            fontproperties=font_props("bold", 28),
            path_effects=_STROKE,
        )

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
            fontsize=32,
            weight="bold",
        )

    if has_route:
        route_ax = fig.add_axes([0.17, 0.34, 0.66, 0.40])
        render_route(route_ax, activity, RouteStyle(mode=route_mode, line_width=7.0))

    if summary is not None:
        baseline_y = 0.18 if has_route else 0.42
        stats = [
            ("Distance", format_distance_km(summary.distance_km), 0.20),
            ("Pace", format_pace(summary.avg_pace_min_per_km), 0.50),
            ("Time", format_duration(summary.moving_time_s), 0.80),
        ]
        for label, value, xpos in stats:
            fig.text(
                xpos,
                baseline_y + 0.045,
                label,
                color=style.text_color,
                ha="center",
                va="center",
                fontsize=16,
                alpha=0.72,
                weight="bold",
            )
            fig.text(
                xpos,
                baseline_y,
                value,
                color=style.text_color,
                ha="center",
                va="center",
                fontsize=21,
                weight="heavy",
            )

    save_figure(fig, output_path, style)
