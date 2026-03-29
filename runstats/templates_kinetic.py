from __future__ import annotations

from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.patheffects as pe

from .models import ActivityData, ActivitySummary
from .template_support import (
    activity_date_str,
    fmt_duration_colon,
    fmt_pace_apos,
    font_props,
    make_figure,
    save_figure,
)
from .templates import TemplateStyle

_LIME = "#f3ffca"
_CORAL = "#ff734a"
_INK = (14 / 255.0, 14 / 255.0, 14 / 255.0, 0.45)


def render_kinetic_glass(
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
        route_color=_LIME,
        accent_color=_LIME,
    )
    fig = make_figure(style)

    _draw_metadata(fig, activity, location)

    if activity.point_count >= 2:
        route_ax = fig.add_axes([0.10, 0.33, 0.80, 0.47])
        _render_kinetic_route(route_ax, activity)

    if summary is not None:
        _draw_editorial_card(fig, summary)

    save_figure(fig, output_path, style)


def _draw_metadata(fig, activity: ActivityData, location: str | None) -> None:
    if location:
        fig.text(
            0.5,
            0.955,
            location.upper(),
            color=_LIME,
            ha="center",
            va="center",
            fontproperties=font_props("bold", 12),
        )
    fig.text(
        0.5,
        0.935,
        activity_date_str(activity),
        color=(1, 1, 1, 0.58),
        ha="center",
        va="center",
        fontproperties=font_props("medium", 10),
    )


def _render_kinetic_route(ax, activity: ActivityData) -> None:
    lons = activity.longitudes
    lats = activity.latitudes

    # Faint structural trace behind the active line.
    ax.plot(
        lons,
        lats,
        color=(1, 1, 1, 0.05),
        linewidth=12,
        solid_capstyle="round",
        solid_joinstyle="round",
        zorder=1,
    )

    (line,) = ax.plot(
        lons,
        lats,
        color=_LIME,
        linewidth=3.6,
        linestyle=(0, (7, 5)),
        dash_capstyle="round",
        solid_joinstyle="round",
        alpha=0.96,
        zorder=3,
    )
    line.set_path_effects(
        [
            pe.withStroke(linewidth=9, foreground=(243 / 255.0, 1.0, 202 / 255.0, 0.08)),
            pe.withStroke(linewidth=6, foreground=(243 / 255.0, 1.0, 202 / 255.0, 0.16)),
            pe.Normal(),
        ]
    )

    ax.plot(
        lons[0],
        lats[0],
        "o",
        color=_LIME,
        markersize=6,
        zorder=5,
        markeredgewidth=0,
    )

    peak_index = _peak_speed_index(activity)
    if peak_index is not None:
        ax.plot(
            lons[peak_index],
            lats[peak_index],
            "o",
            color=_CORAL,
            markersize=4.5,
            zorder=6,
            markeredgewidth=0,
        )
        ax.annotate(
            "PACE PEAK",
            xy=(lons[peak_index], lats[peak_index]),
            xytext=(8, 0),
            textcoords="offset points",
            color=_CORAL,
            fontsize=8,
            fontweight="bold",
            va="center",
            ha="left",
            zorder=6,
        )

    lon_min, lon_max = min(lons), max(lons)
    lat_min, lat_max = min(lats), max(lats)
    width = max(lon_max - lon_min, 1e-9)
    height = max(lat_max - lat_min, 1e-9)
    ax.set_xlim(lon_min - width * 0.10, lon_max + width * 0.10)
    ax.set_ylim(lat_min - height * 0.10, lat_max + height * 0.10)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.patch.set_alpha(0.0)


def _peak_speed_index(activity: ActivityData) -> int | None:
    best_index: int | None = None
    best_speed = 0.0
    for idx, point in enumerate(activity.points):
        speed = point.speed_mps or 0.0
        if speed > best_speed:
            best_speed = speed
            best_index = idx
    return best_index if best_speed > 0.1 else None


def _draw_editorial_card(fig, summary: ActivitySummary) -> None:
    ax = fig.add_axes([0, 0, 1, 1])
    ax.axis("off")
    ax.patch.set_alpha(0.0)

    card_x, card_y = 0.055, 0.055
    card_w, card_h = 0.890, 0.235

    ax.add_patch(
        mpatches.FancyBboxPatch(
            (card_x, card_y),
            card_w,
            card_h,
            boxstyle="round,pad=0.010,rounding_size=0.018",
            facecolor=_INK,
            edgecolor=(1, 1, 1, 0.06),
            linewidth=1.0,
            transform=ax.transAxes,
        )
    )
    ax.add_patch(
        mpatches.FancyBboxPatch(
            (card_x + 0.004, card_y + 0.004),
            card_w - 0.008,
            card_h - 0.008,
            boxstyle="round,pad=0.008,rounding_size=0.016",
            facecolor=(1, 1, 1, 0.015),
            edgecolor=(1, 1, 1, 0.04),
            linewidth=0.8,
            transform=ax.transAxes,
        )
    )

    fig.text(
        0.09,
        0.258,
        "TOTAL DISTANCE",
        color=(1, 1, 1, 0.46),
        ha="left",
        va="center",
        fontproperties=font_props("bold", 11),
    )
    fig.text(
        0.09,
        0.214,
        f"{summary.distance_km:.2f}",
        color="#FFFFFF",
        ha="left",
        va="center",
        fontproperties=font_props("heavy", 64),
    )
    fig.text(
        0.415,
        0.206,
        "KM",
        color=_LIME,
        ha="left",
        va="center",
        fontproperties=font_props("medium", 22),
    )

    _draw_progress_bar(fig, summary)

    label_y = 0.114
    value_y = 0.081
    pace_x = 0.09
    time_x = 0.54

    fig.text(
        pace_x,
        label_y,
        "AVG PACE",
        color=(1, 1, 1, 0.46),
        ha="left",
        va="center",
        fontproperties=font_props("bold", 11),
    )
    fig.text(
        pace_x,
        value_y,
        fmt_pace_apos(summary.avg_pace_min_per_km),
        color="#FFFFFF",
        ha="left",
        va="center",
        fontproperties=font_props("bold", 28),
    )
    fig.text(
        0.305,
        value_y - 0.003,
        "/KM",
        color=(1, 1, 1, 0.60),
        ha="left",
        va="center",
        fontproperties=font_props("bold", 11),
    )

    fig.text(
        time_x,
        label_y,
        "DURATION",
        color=(1, 1, 1, 0.46),
        ha="left",
        va="center",
        fontproperties=font_props("bold", 11),
    )
    fig.text(
        time_x,
        value_y,
        fmt_duration_colon(summary.moving_time_s),
        color="#FFFFFF",
        ha="left",
        va="center",
        fontproperties=font_props("bold", 28),
    )

    fig.text(
        0.09,
        0.035,
        "PERFORMANCE // OVERLAY",
        color=(1, 1, 1, 0.32),
        ha="left",
        va="center",
        fontproperties=font_props("bold", 9),
    )
    fig.text(
        0.92,
        0.036,
        "•",
        color=(1, 1, 1, 0.35),
        ha="center",
        va="center",
        fontproperties=font_props("bold", 14),
    )


def _draw_progress_bar(fig, summary: ActivitySummary) -> None:
    track = fig.add_axes([0.09, 0.152, 0.82, 0.008])
    track.axis("off")
    track.patch.set_alpha(0.0)

    track.add_patch(
        mpatches.FancyBboxPatch(
            (0, 0),
            1,
            1,
            boxstyle="round,pad=0.0,rounding_size=0.9",
            facecolor=(1, 1, 1, 0.10),
            edgecolor="none",
            transform=track.transAxes,
        )
    )

    progress = min(max(summary.distance_km / 12.5, 0.35), 0.92)
    progress_ax = fig.add_axes([0.09, 0.152, 0.82 * progress, 0.008])
    progress_ax.axis("off")
    progress_ax.patch.set_alpha(0.0)
    progress_ax.add_patch(
        mpatches.FancyBboxPatch(
            (0, 0),
            1,
            1,
            boxstyle="round,pad=0.0,rounding_size=0.9",
            facecolor=_LIME,
            edgecolor="none",
            transform=progress_ax.transAxes,
        )
    )

    fig.lines.append(
        mlines.Line2D(
            [0.09, 0.09 + 0.82 * progress],
            [0.156, 0.156],
            transform=fig.transFigure,
            color=(1, 1, 1, 0.10),
            linewidth=1.0,
        )
    )
