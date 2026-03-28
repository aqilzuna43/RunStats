from __future__ import annotations

from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import numpy as np

from .models import ActivityData, ActivitySummary
from .render import RouteStyle, render_route
from .template_support import (
    activity_date_str,
    fmt_duration_colon,
    fmt_optional,
    fmt_pace_apos,
    font_props,
    make_figure,
    save_figure,
)
from .templates import TemplateStyle, _diagonal_gradient_rgba, _horiz_gradient_img


def render_neon_split(
    activity: ActivityData,
    output_path: str | Path,
    route_mode: str,
    summary: ActivitySummary | None,
    location: str | None = None,
) -> None:
    style = TemplateStyle(canvas_width_px=1080, canvas_height_px=1080, dpi=200)
    fig = make_figure(style)

    W, H = style.canvas_width_px, style.canvas_height_px

    # -- Background: solid #0a0a0a rounded card --
    rgba_bg = _diagonal_gradient_rgba(
        "#0a0a0a", "#0a0a0a", W, H, angle_deg=0,
        card_x0=0.0, card_y0=0.0, card_x1=1.0, card_y1=1.0,
        corner_r=0.055,
    )
    bg_ax = fig.add_axes([0, 0, 1, 1])
    bg_ax.imshow(rgba_bg, aspect="auto", extent=[0, 1, 0, 1],
                 transform=bg_ax.transAxes, origin="upper")
    bg_ax.axis("off")

    # -- Smooth radial glow (replaces discrete circles) --
    from .template_support import radial_glow_image
    glow_rgba = radial_glow_image(W, H, cx_frac=1.0, cy_frac=0.0,
                                   radius_frac=0.35, color_hex="#ff6b35",
                                   peak_alpha=0.25)
    glow_ax = fig.add_axes([0, 0, 1, 1])
    glow_ax.imshow(glow_rgba, aspect="auto", extent=[0, 1, 0, 1],
                   transform=glow_ax.transAxes, origin="upper")
    glow_ax.axis("off")

    if summary is not None:
        # -- "MORNING RUN" label --
        fig.text(0.085, 0.835, "MORNING RUN",
                 color=(1, 1, 1, 0.30), ha="left", va="center",
                 fontsize=12, weight="bold")

        # -- Distance hero --
        num_str = f"{summary.distance_km:.2f}"
        fig.text(0.085, 0.728, num_str,
                 color="#FFFFFF", ha="left", va="center",
                 fontproperties=font_props("heavy", 80))
        dist_x_end = 0.085 + len(num_str) * 0.064
        fig.text(dist_x_end, 0.712, "km",
                 color=(1, 1, 1, 0.30), ha="left", va="center",
                 fontproperties=font_props("semibold", 22))

        # -- Mini route (top-right, transparent background) --
        if activity.point_count >= 2:
            route_ax = fig.add_axes([0.63, 0.595, 0.295, 0.265])
            render_route(route_ax, activity,
                         RouteStyle(mode="solid", color="#ff6b35", line_width=2.5))
            # Ensure transparent background
            route_ax.set_facecolor("none")
            route_ax.patch.set_visible(False)
            for spine in route_ax.spines.values():
                spine.set_visible(False)

            from .template_support import draw_route_markers
            draw_route_markers(route_ax, activity, "#ff6b35", "#ff3366", marker_size=5)

        # -- Pace highlight bar (gradient orange->pink) --
        bar_img = _horiz_gradient_img("#ff6b35", "#ff3366", W=512)
        bar_ax = fig.add_axes([0.055, 0.425, 0.890, 0.160])
        bar_ax.set_xlim(0, 1)
        bar_ax.set_ylim(0, 1)
        bar_ax.axis("off")
        im = bar_ax.imshow(bar_img, aspect="auto", extent=[0, 1, 0, 1], origin="upper")
        clip = mpatches.FancyBboxPatch(
            (0.0, 0.0), 1.0, 1.0,
            boxstyle="round,pad=0.0,rounding_size=0.18",
            transform=bar_ax.transAxes,
            facecolor="none", edgecolor="none",
        )
        bar_ax.add_patch(clip)
        im.set_clip_path(clip)

        # Bar text: AVG PACE (left)
        fig.text(0.095, 0.533, "AVG PACE",
                 color=(1, 1, 1, 0.60), ha="left", va="center",
                 fontsize=11, weight="bold")
        fig.text(0.095, 0.472, fmt_pace_apos(summary.avg_pace_min_per_km) + " /km",
                 color="#FFFFFF", ha="left", va="center",
                 fontproperties=font_props("heavy", 34))

        # Bar text: DURATION (right)
        fig.text(0.905, 0.533, "DURATION",
                 color=(1, 1, 1, 0.60), ha="right", va="center",
                 fontsize=11, weight="bold")
        fig.text(0.905, 0.472, fmt_duration_colon(summary.moving_time_s),
                 color="#FFFFFF", ha="right", va="center",
                 fontproperties=font_props("heavy", 34))

        # -- Bottom stats grid: 3 columns --
        elev_str = (
            f"{summary.elevation_gain_m:+.0f}m"
            if summary.elevation_gain_m is not None else "N/A"
        )
        grid = [
            ("CALORIES",   fmt_optional(summary.total_calories_kcal, " kcal")),
            ("HEART RATE", fmt_optional(summary.avg_heart_rate_bpm, " bpm")),
            ("ELEVATION",  elev_str),
        ]
        xs = [0.22, 0.50, 0.78]
        for i, ((lbl, val), x) in enumerate(zip(grid, xs)):
            fig.text(x, 0.353, lbl,
                     color=(1, 1, 1, 0.25), ha="center", va="center",
                     fontsize=11, weight="bold")
            fig.text(x, 0.278, val,
                     color="#FFFFFF", ha="center", va="center",
                     fontproperties=font_props("bold", 24))
            # Column dividers (increased visibility)
            if i > 0:
                div_x = (xs[i - 1] + x) / 2
                fig.lines.append(mlines.Line2D(
                    [div_x, div_x], [0.24, 0.39],
                    transform=fig.transFigure,
                    color="#FFFFFF", linewidth=1.2, alpha=0.12,
                ))

        # -- Footer --
        date_str = activity_date_str(activity)
        fig.text(0.085, 0.125, date_str,
                 color=(1, 1, 1, 0.20), ha="left", va="center",
                 fontsize=12, weight="medium")
        if location:
            fig.text(0.915, 0.125, location,
                     color=(1, 1, 1, 0.20), ha="right", va="center",
                     fontsize=12, weight="medium")

    save_figure(fig, output_path, style)
