from __future__ import annotations

from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt

from .models import ActivityData, ActivitySummary
from .template_support import (
    draw_route_markers,
    fmt_duration_colon,
    fmt_optional,
    fmt_pace_apos,
    font_props,
    make_figure,
    save_figure,
)
from .templates import TemplateStyle, _diagonal_gradient_rgba


def render_glass_slab(
    activity: ActivityData,
    output_path: str | Path,
    route_mode: str,
    summary: ActivitySummary | None,
    location: str | None = None,
) -> None:
    style = TemplateStyle(canvas_width_px=1080, canvas_height_px=1350, dpi=200)
    fig = make_figure(style)

    # -- Transparent route section --
    if activity.point_count >= 2:
        route_ax = fig.add_axes([0.18, 0.45, 0.64, 0.37])
        _render_dotted_route(route_ax, activity)
        draw_route_markers(route_ax, activity, "#4ade80", "#f97316", marker_size=6)

    # -- Frosted glass stats card with depth layers --
    glass_ax = fig.add_axes([0, 0, 1, 1])
    glass_ax.axis("off")
    glass_ax.patch.set_alpha(0.0)

    card_pos = (0.065, 0.075)
    card_w, card_h = 0.870, 0.395

    # Outer halo for glass depth
    glass_halo = mpatches.FancyBboxPatch(
        card_pos, card_w, card_h,
        boxstyle="round,pad=0.01,rounding_size=0.04",
        facecolor="none",
        edgecolor=(1, 1, 1, 0.06),
        linewidth=4,
        transform=glass_ax.transAxes,
    )
    glass_ax.add_patch(glass_halo)

    # Main glass card
    glass_card = mpatches.FancyBboxPatch(
        card_pos, card_w, card_h,
        boxstyle="round,pad=0.01,rounding_size=0.04",
        facecolor=(1, 1, 1, 0.10),
        edgecolor=(1, 1, 1, 0.12),
        linewidth=1.5,
        transform=glass_ax.transAxes,
    )
    glass_ax.add_patch(glass_card)

    # Inner highlight for glass shine
    inset = 0.008
    glass_inner = mpatches.FancyBboxPatch(
        (card_pos[0] + inset, card_pos[1] + inset),
        card_w - 2 * inset, card_h - 2 * inset,
        boxstyle="round,pad=0.005,rounding_size=0.035",
        facecolor="none",
        edgecolor=(1, 1, 1, 0.08),
        linewidth=0.8,
        transform=glass_ax.transAxes,
    )
    glass_ax.add_patch(glass_inner)

    # Specular top-edge highlight
    top_edge_y = card_pos[1] + card_h - 0.015
    highlight = mlines.Line2D(
        [card_pos[0] + 0.08, card_pos[0] + card_w - 0.08],
        [top_edge_y, top_edge_y],
        transform=fig.transFigure,
        color=(1, 1, 1, 0.15),
        linewidth=1,
    )
    fig.lines.append(highlight)

    if summary is not None:
        # Hero stat -- centered distance
        num_str = f"{summary.distance_km:.2f}"
        hero_y = card_pos[1] + card_h * 0.72
        fig.text(
            0.5,
            hero_y,
            num_str,
            color="#FFFFFF",
            ha="center",
            va="center",
            fontproperties=font_props("bold", 62),
            zorder=6,
        )
        fig.text(
            0.86,
            hero_y - 0.012,
            "KM",
            color="#A3AAA6",
            ha="right",
            va="center",
            fontproperties=font_props("medium", 24),
            zorder=5,
        )

        # Gradient-fade divider
        from .template_support import gradient_fade_line
        gradient_fade_line(fig, 0.290, 0.12, 0.88, "#FFFFFF", peak_alpha=0.18)

        # 4-stat row
        elev_str = (
            f"+{summary.elevation_gain_m:.0f}m"
            if summary.elevation_gain_m is not None else "N/A"
        )
        stats = [
            ("PACE", fmt_pace_apos(summary.avg_pace_min_per_km)),
            ("TIME", fmt_duration_colon(summary.moving_time_s)),
            ("CAL",  fmt_optional(summary.total_calories_kcal, "")),
            ("ELEV", elev_str),
        ]
        xs = [0.175, 0.392, 0.608, 0.825]
        for (label, value), x in zip(stats, xs):
            fig.text(x, 0.237, label,
                     color="#A3AAA6", ha="center", va="center",
                     fontsize=13, weight="semibold")
            fig.text(x, 0.172, value,
                     color="#FFFFFF", ha="center", va="center",
                     fontproperties=font_props("semibold", 20))

    if location:
        location_length = len(location)
        pill_width = min(max(0.25, 0.15 + location_length * 0.011), 0.56)
        pill_height = 0.038
        pill_x = 0.5 - pill_width / 2
        pill_y = card_pos[1] + 0.020
        font_size = 11
        if location_length >= 24:
            font_size = 10
        if location_length >= 32:
            font_size = 9
        pill_bg = mpatches.FancyBboxPatch(
            (pill_x, pill_y), pill_width, pill_height,
            boxstyle="round,pad=0.005,rounding_size=0.030",
            facecolor=(0, 0, 0, 0.22),
            edgecolor=(1, 1, 1, 0.08),
            linewidth=0.8,
            transform=glass_ax.transAxes,
        )
        glass_ax.add_patch(pill_bg)
        fig.text(
            0.5,
            pill_y + pill_height / 2,
            location,
            color="#B9C0BC",
            ha="center",
            va="center",
            fontsize=font_size,
            weight="medium",
        )

    save_figure(fig, output_path, style)


def _render_dotted_route(ax: plt.Axes, activity: ActivityData) -> None:
    lons = activity.longitudes
    lats = activity.latitudes

    ax.plot(
        lons,
        lats,
        color="#4ade80",
        linewidth=3.0,
        dash_capstyle="round",
        solid_joinstyle="round",
        alpha=0.72,
        zorder=3,
    )
    _apply_route_limits(ax, lons, lats)
    ax.set_aspect("equal")
    ax.axis("off")
    ax.patch.set_alpha(0.0)


def _apply_route_limits(
    ax: plt.Axes,
    lons: tuple[float, ...],
    lats: tuple[float, ...],
    padding_ratio: float = 0.015,
) -> None:
    lon_min, lon_max = min(lons), max(lons)
    lat_min, lat_max = min(lats), max(lats)

    width = max(lon_max - lon_min, 1e-9)
    height = max(lat_max - lat_min, 1e-9)
    padding_x = width * padding_ratio
    padding_y = height * padding_ratio

    ax.set_xlim(lon_min - padding_x, lon_max + padding_x)
    ax.set_ylim(lat_min - padding_y, lat_max + padding_y)
