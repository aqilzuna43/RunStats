from __future__ import annotations

from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.patches as mpatches

from .models import ActivityData, ActivitySummary
from .template_support import (
    activity_date_str,
    draw_icon_shape,
    fmt_duration_colon,
    fmt_optional,
    fmt_pace_apos,
    font_props,
    make_figure,
    save_figure,
)
from .templates import TemplateStyle, _hex_to_rgb


def render_clipboard_card(
    activity: ActivityData,
    output_path: str | Path,
    summary: ActivitySummary | None,
    location: str | None = None,
) -> None:
    style = TemplateStyle(canvas_width_px=1080, canvas_height_px=1350, dpi=200)
    fig = make_figure(style)

    card_ax = fig.add_axes([0, 0, 1, 1])
    card_ax.axis("off")
    card_ax.patch.set_alpha(0.0)

    # -- White card with orange border --
    card = mpatches.FancyBboxPatch(
        (0.07, 0.05), 0.86, 0.87,
        boxstyle="round,pad=0.0,rounding_size=0.038",
        facecolor="#FFFFFF",
        edgecolor="#ff6b35",
        linewidth=3.5,
        transform=card_ax.transAxes,
    )
    card_ax.add_patch(card)

    # -- Square off top-left corner (concept: borderRadius "0 12px 12px 12px") --
    corner_patch = mpatches.Rectangle(
        (0.07, 0.89), 0.06, 0.03,
        facecolor="#FFFFFF",
        edgecolor="#ff6b35",
        linewidth=3.5,
        transform=card_ax.transAxes,
        zorder=card.get_zorder() + 0.1,
    )
    card_ax.add_patch(corner_patch)
    # White fill to cover inner border overlap
    corner_fill = mpatches.Rectangle(
        (0.073, 0.893), 0.054, 0.024,
        facecolor="#FFFFFF",
        edgecolor="none",
        transform=card_ax.transAxes,
        zorder=card.get_zorder() + 0.2,
    )
    card_ax.add_patch(corner_fill)

    # -- "RUN" tab --
    tab = mpatches.FancyBboxPatch(
        (0.177, 0.918), 0.135, 0.042,
        boxstyle="round,pad=0.0,rounding_size=0.025",
        facecolor="#ff6b35",
        edgecolor="none",
        transform=card_ax.transAxes,
    )
    card_ax.add_patch(tab)
    fig.text(0.244, 0.939, "RUN",
             color="#FFFFFF", ha="center", va="center",
             fontsize=12, weight="bold")

    # -- Orange header band --
    header = mpatches.Rectangle(
        (0.07, 0.855), 0.86, 0.063,
        facecolor="#ff6b35",
        edgecolor="none",
        transform=card_ax.transAxes,
    )
    card_ax.add_patch(header)

    date_str = activity_date_str(activity)
    fig.text(0.115, 0.886, date_str,
             color="#FFFFFF", ha="left", va="center",
             fontsize=14, weight="bold")
    if location:
        fig.text(0.890, 0.886, location,
                 color=(1, 1, 1, 0.70), ha="right", va="center",
                 fontsize=12, weight="medium")

    if summary is not None:
        # -- "TOTAL DISTANCE" label --
        fig.text(0.50, 0.793, "TOTAL DISTANCE",
                 color="#999999", ha="center", va="center",
                 fontsize=13, weight="semibold")

        # -- Distance hero --
        num_str = f"{summary.distance_km:.2f}"
        fig.text(0.463, 0.737, num_str,
                 color="#1a1a1a", ha="right", va="center",
                 fontproperties=font_props("bold", 56))
        fig.text(0.476, 0.722, "km",
                 color="#999999", ha="left", va="center",
                 fontsize=18)

        # -- Dashed divider (increased visibility) --
        dash_line = mlines.Line2D(
            [0.09, 0.91], [0.695, 0.695],
            transform=fig.transFigure,
            color="#ff6b35", linewidth=2.0, alpha=0.35, linestyle="--",
        )
        fig.lines.append(dash_line)

        # -- 5 stat rows with geometric icons --
        elev_str = (
            f"+{summary.elevation_gain_m:.0f}m"
            if summary.elevation_gain_m is not None else "N/A"
        )
        rows = [
            ("arrow_up_right", "Distance",  f"{summary.distance_km:.2f} km", "#ff6b35"),
            ("clock",          "Duration",  fmt_duration_colon(summary.moving_time_s), "#ff6b35"),
            ("target",         "Avg Pace",  fmt_pace_apos(summary.avg_pace_min_per_km) + " /km", "#ff6b35"),
            ("heart",          "Heart Rate", fmt_optional(summary.avg_heart_rate_bpm, " bpm"), "#ff4444"),
            ("mountain",       "Elevation", elev_str, "#ff6b35"),
        ]
        y_positions = [0.624, 0.530, 0.436, 0.342, 0.248]
        for (icon_type, label, value, accent), y in zip(rows, y_positions):
            # Icon background box (increased visibility)
            r, g, b = _hex_to_rgb(accent)
            icon_box = mpatches.FancyBboxPatch(
                (0.095, y - 0.030), 0.082, 0.058,
                boxstyle="round,pad=0.0,rounding_size=0.020",
                facecolor=(r, g, b, 0.14),
                edgecolor="none",
                transform=card_ax.transAxes,
            )
            card_ax.add_patch(icon_box)

            # Geometric icon shape
            draw_icon_shape(fig, 0.136, y + 0.001, icon_type, accent, size=0.018)

            # Label
            fig.text(0.220, y + 0.001, label,
                     color="#888888", ha="left", va="center",
                     fontsize=16, weight="medium")
            # Value
            fig.text(0.910, y + 0.001, value,
                     color="#1a1a1a", ha="right", va="center",
                     fontproperties=font_props("bold", 20))

            # Row divider (skip last)
            if y != y_positions[-1]:
                div = mlines.Line2D(
                    [0.09, 0.91], [y - 0.040, y - 0.040],
                    transform=fig.transFigure,
                    color="#000000", linewidth=0.8, alpha=0.06,
                )
                fig.lines.append(div)

    save_figure(fig, output_path, style)
