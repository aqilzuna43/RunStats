from __future__ import annotations

import math
from dataclasses import dataclass
from pathlib import Path

import matplotlib.lines as mlines
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import FancyBboxPatch

from .metrics import format_distance_km, format_duration, format_pace
from .models import ActivityData, ActivitySummary
from .render import RouteStyle, render_route
from .template_support import (
    activity_date_str as _activity_date_str,
    add_separator_line as _add_separator_line,
    add_stat_row as _add_stat_row,
    fmt_duration_colon as _fmt_duration_colon,
    fmt_optional as _fmt_optional,
    fmt_pace_apos as _fmt_pace_apos,
    font_props as _font_props,
    make_figure as _make_figure,
    save_figure as _save_figure,
)


DEFAULT_TITLE = "RELENTLESS"
TEMPLATE_NAMES = ("story_overlay", "clean_card", "glass_slab", "clipboard_card", "neon_split")


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
    if template_name == "glass_slab":
        _render_glass_slab(activity, output_path, route_mode, summary)
        return
    if template_name == "clipboard_card":
        _render_clipboard_card(activity, output_path, summary)
        return
    if template_name == "neon_split":
        _render_neon_split(activity, output_path, route_mode, summary)
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
    has_route = activity.point_count >= 2

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


def _hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    h = hex_color.lstrip("#")
    return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))


def _diagonal_gradient_rgba(
    hex1: str,
    hex2: str,
    W: int,
    H: int,
    angle_deg: float,
    card_x0: float,
    card_y0: float,
    card_x1: float,
    card_y1: float,
    corner_r: float = 0.04,
) -> np.ndarray:
    """
    Create an RGBA image (H×W×4) with a diagonal gradient inside a rounded-rectangle
    region and alpha=0 everywhere outside it.
    """
    c1 = np.array(_hex_to_rgb(hex1))
    c2 = np.array(_hex_to_rgb(hex2))

    # gradient value t in [0,1] across the full canvas
    xx = np.linspace(0, 1, W)
    yy = np.linspace(0, 1, H)
    XX, YY = np.meshgrid(xx, yy)
    rad = math.radians(angle_deg)
    t = XX * math.cos(rad) + (1.0 - YY) * math.sin(rad)
    t = (t - t.min()) / (t.max() - t.min() + 1e-9)

    rgb = c1[None, None, :] * (1 - t[:, :, None]) + c2[None, None, :] * t[:, :, None]

    # rounded-rectangle alpha mask
    px0, py0 = int(card_x0 * W), int(card_y0 * H)
    px1, py1 = int(card_x1 * W), int(card_y1 * H)
    pr = int(corner_r * min(W, H))

    mask = np.zeros((H, W), dtype=float)
    # central cross
    mask[py0 + pr : py1 - pr, px0:px1] = 1.0
    mask[py0:py1, px0 + pr : px1 - pr] = 1.0
    # four corners
    for cx, cy in [
        (px0 + pr, py0 + pr),
        (px1 - pr, py0 + pr),
        (px0 + pr, py1 - pr),
        (px1 - pr, py1 - pr),
    ]:
        ys = np.arange(max(0, cy - pr), min(H, cy + pr))
        xs = np.arange(max(0, cx - pr), min(W, cx + pr))
        YY2, XX2 = np.meshgrid(ys, xs, indexing="ij")
        inside = (XX2 - cx) ** 2 + (YY2 - cy) ** 2 <= pr ** 2
        mask[ys[0] : ys[-1] + 1, xs[0] : xs[-1] + 1] = np.maximum(
            mask[ys[0] : ys[-1] + 1, xs[0] : xs[-1] + 1], inside.astype(float)
        )

    rgba = np.zeros((H, W, 4), dtype=float)
    rgba[:, :, :3] = np.clip(rgb, 0, 1)
    rgba[:, :, 3] = mask
    return rgba


def _horiz_gradient_img(hex1: str, hex2: str, W: int = 512) -> np.ndarray:
    """1×W×3 horizontal gradient array."""
    c1 = np.array(_hex_to_rgb(hex1))
    c2 = np.array(_hex_to_rgb(hex2))
    t = np.linspace(0, 1, W)
    img = c1[None, :] * (1 - t[:, None]) + c2[None, :] * t[:, None]
    return np.clip(img, 0, 1)[None, :, :]


# ─────────────────────────────────────────────
# CONCEPT A — "Glass Slab"
# linear-gradient(145deg, #1a3a2a → #0d1f15) card, route peek-through,
# frosted-glass stats section at bottom.
# ─────────────────────────────────────────────
def _render_glass_slab(
    activity: ActivityData,
    output_path: str | Path,
    route_mode: str,
    summary: ActivitySummary | None,
) -> None:
    # 1080×1350 — 4:5 portrait matches the card's natural proportions
    style = TemplateStyle(canvas_width_px=1080, canvas_height_px=1350, dpi=200)
    fig = _make_figure(style)

    W, H = style.canvas_width_px, style.canvas_height_px

    # — Background: linear-gradient(145deg, #1a3a2a 0%, #0d1f15 100%)
    #   rendered only inside the rounded-rectangle card (alpha=0 outside)
    rgba_bg = _diagonal_gradient_rgba(
        "#1a3a2a", "#0d1f15", W, H, angle_deg=145,
        card_x0=0.04, card_y0=0.04, card_x1=0.96, card_y1=0.96,
        corner_r=0.045,
    )
    bg_ax = fig.add_axes([0, 0, 1, 1])
    bg_ax.imshow(rgba_bg, aspect="auto", extent=[0, 1, 0, 1],
                 transform=bg_ax.transAxes, origin="upper")
    bg_ax.axis("off")

    # — Simulated map section: route fills top portion (y 0.44–0.94) —
    if activity.point_count >= 2:
        route_ax = fig.add_axes([0.06, 0.44, 0.88, 0.48])
        render_route(route_ax, activity, RouteStyle(mode=route_mode, color="#4ade80", line_width=5.0))

    # — Date + location pill  (top-left, semi-transparent dark pill) —
    date_str = _activity_date_str(activity)
    pill_ax = fig.add_axes([0, 0, 1, 1])
    pill_ax.axis("off")
    pill_ax.patch.set_alpha(0.0)
    pill_bg = mpatches.FancyBboxPatch(
        (0.065, 0.905), 0.40, 0.052,
        boxstyle="round,pad=0.005,rounding_size=0.035",
        facecolor=(0, 0, 0, 0.35),
        edgecolor="none",
        transform=pill_ax.transAxes,
    )
    pill_ax.add_patch(pill_bg)
    fig.text(0.100, 0.932, "●", color="#4ade80", ha="left", va="center", fontsize=12)
    fig.text(0.130, 0.932, date_str,
             color=(1, 1, 1, 0.75), ha="left", va="center", fontsize=14, weight="medium")

    # — Frosted glass stats card (overlaps map bottom by ~40 px equivalent) —
    glass_ax = fig.add_axes([0, 0, 1, 1])
    glass_ax.axis("off")
    glass_ax.patch.set_alpha(0.0)
    glass_card = mpatches.FancyBboxPatch(
        (0.065, 0.075), 0.870, 0.395,
        boxstyle="round,pad=0.01,rounding_size=0.04",
        facecolor=(1, 1, 1, 0.08),
        edgecolor=(1, 1, 1, 0.12),
        linewidth=1.5,
        transform=glass_ax.transAxes,
    )
    glass_ax.add_patch(glass_card)

    if summary is not None:
        # Hero stat — distance number (52 px weight:700) + "KM" unit (18 px, 50% opacity)
        num_str = f"{summary.distance_km:.2f}"
        fig.text(0.455, 0.388, num_str,
                 color="#FFFFFF", ha="right", va="center",
                 fontproperties=_font_props("bold", 62))
        fig.text(0.468, 0.373, "KM",
                 color=(1, 1, 1, 0.50), ha="left", va="center",
                 fontproperties=_font_props("medium", 22))

        # Divider — gradient fade (transparent → white 15% → transparent)
        _add_separator_line(
            fig, 0.290, 0.12, 0.88,
            TemplateStyle(canvas_width_px=W, canvas_height_px=H, dpi=200,
                          accent_color="#FFFFFF", accent_alpha=0.15),
        )

        # 4-stat row  (label 10 px 35% opacity, value 16 px white)
        elev_str = (
            f"+{summary.elevation_gain_m:.0f}m"
            if summary.elevation_gain_m is not None else "N/A"
        )
        stats = [
            ("PACE", _fmt_pace_apos(summary.avg_pace_min_per_km)),
            ("TIME", _fmt_duration_colon(summary.moving_time_s)),
            ("CAL",  _fmt_optional(summary.total_calories_kcal, "")),
            ("ELEV", elev_str),
        ]
        xs = [0.175, 0.392, 0.608, 0.825]
        for (label, value), x in zip(stats, xs):
            fig.text(x, 0.237, label,
                     color=(1, 1, 1, 0.35), ha="center", va="center",
                     fontsize=13, weight="semibold")
            fig.text(x, 0.172, value,
                     color="#FFFFFF", ha="center", va="center",
                     fontproperties=_font_props("semibold", 20))

    _save_figure(fig, output_path, style)


# ─────────────────────────────────────────────
# CONCEPT B — "Clipboard Card"
# White card, orange 2.5 px border, RUN tab, stacked stat rows.
# ─────────────────────────────────────────────
def _render_clipboard_card(
    activity: ActivityData,
    output_path: str | Path,
    summary: ActivitySummary | None,
) -> None:
    # 1080×1350 — matches natural card proportions (320:400 scaled up)
    style = TemplateStyle(canvas_width_px=1080, canvas_height_px=1350, dpi=200)
    fig = _make_figure(style)

    card_ax = fig.add_axes([0, 0, 1, 1])
    card_ax.axis("off")
    card_ax.patch.set_alpha(0.0)

    # White card — borderRadius "0 12px 12px 12px", border: "2.5px solid #ff6b35"
    card = mpatches.FancyBboxPatch(
        (0.07, 0.05), 0.86, 0.87,
        boxstyle="round,pad=0.0,rounding_size=0.038",
        facecolor="#FFFFFF",
        edgecolor="#ff6b35",
        linewidth=3.5,
        transform=card_ax.transAxes,
    )
    card_ax.add_patch(card)

    # "RUN" tab — width:70, height:24, borderRadius "8px 8px 0 0", marginLeft:40
    # In figure coords: tab left ≈ card_left + (40/320)*card_width
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

    # Orange header band — padding: "12px 18px"
    header = mpatches.Rectangle(
        (0.07, 0.855), 0.86, 0.063,
        facecolor="#ff6b35",
        edgecolor="none",
        transform=card_ax.transAxes,
    )
    card_ax.add_patch(header)

    date_str = _activity_date_str(activity)
    # date: left, 11px, weight:700, white
    fig.text(0.115, 0.886, date_str,
             color="#FFFFFF", ha="left", va="center",
             fontsize=14, weight="bold")

    if summary is not None:
        # "TOTAL DISTANCE" label — 10px, #999, weight:600
        fig.text(0.50, 0.793, "TOTAL DISTANCE",
                 color="#999999", ha="center", va="center",
                 fontsize=13, weight="semibold")

        # Distance hero — 44px, weight:700, #1a1a1a + "km" suffix 16px #999
        num_str = f"{summary.distance_km:.2f}"
        fig.text(0.463, 0.737, num_str,
                 color="#1a1a1a", ha="right", va="center",
                 fontproperties=_font_props("bold", 56))
        fig.text(0.476, 0.722, "km",
                 color="#999999", ha="left", va="center",
                 fontsize=18)

        # Dashed divider — borderBottom "1.5px dashed rgba(255,107,53,0.2)"
        dash_line = mlines.Line2D(
            [0.09, 0.91], [0.695, 0.695],
            transform=fig.transFigure,
            color="#ff6b35", linewidth=1.5, alpha=0.20, linestyle="--",
        )
        fig.lines.append(dash_line)

        # 5 stat rows
        elev_str = (
            f"+{summary.elevation_gain_m:.0f}m"
            if summary.elevation_gain_m is not None else "N/A"
        )
        rows = [
            ("↗", "Distance",  f"{summary.distance_km:.2f} km", "#ff6b35"),
            ("◷", "Duration",  _fmt_duration_colon(summary.moving_time_s), "#ff6b35"),
            ("◎", "Avg Pace",  _fmt_pace_apos(summary.avg_pace_min_per_km) + " /km", "#ff6b35"),
            ("♥", "Heart Rate", _fmt_optional(summary.avg_heart_rate_bpm, " bpm"), "#ff4444"),
            ("▲", "Elevation", elev_str, "#ff6b35"),
        ]
        y_positions = [0.624, 0.530, 0.436, 0.342, 0.248]
        for (icon, label, value, accent), y in zip(rows, y_positions):
            # Icon box — 26×26, borderRadius:6, background: accent+"12" (≈7% opacity)
            r, g, b = _hex_to_rgb(accent)
            icon_box = mpatches.FancyBboxPatch(
                (0.095, y - 0.030), 0.082, 0.058,
                boxstyle="round,pad=0.0,rounding_size=0.020",
                facecolor=(r, g, b, 0.07),
                edgecolor="none",
                transform=card_ax.transAxes,
            )
            card_ax.add_patch(icon_box)
            fig.text(0.136, y + 0.001, icon,
                     color=accent, ha="center", va="center", fontsize=17)
            # label — 12px, #888, weight:500
            fig.text(0.220, y + 0.001, label,
                     color="#888888", ha="left", va="center",
                     fontsize=16, weight="medium")
            # value — 15px, weight:700, #1a1a1a
            fig.text(0.910, y + 0.001, value,
                     color="#1a1a1a", ha="right", va="center",
                     fontproperties=_font_props("bold", 20))

            # Row divider — 1px, rgba(0,0,0,0.06) — skip last row
            if y != y_positions[-1]:
                div = mlines.Line2D(
                    [0.09, 0.91], [y - 0.040, y - 0.040],
                    transform=fig.transFigure,
                    color="#000000", linewidth=0.8, alpha=0.06,
                )
                fig.lines.append(div)

    _save_figure(fig, output_path, style)


# ─────────────────────────────────────────────
# CONCEPT C — "Neon Split"
# #0a0a0a card, orange glow, big distance, orange→pink gradient bar,
# 3-col stat grid, footer.
# ─────────────────────────────────────────────
def _render_neon_split(
    activity: ActivityData,
    output_path: str | Path,
    route_mode: str,
    summary: ActivitySummary | None,
) -> None:
    # 1080×1080 — square card (340:320 ≈ 1:1)
    style = TemplateStyle(canvas_width_px=1080, canvas_height_px=1080, dpi=200)
    fig = _make_figure(style)

    W, H = style.canvas_width_px, style.canvas_height_px

    # — Background: solid #0a0a0a rounded card, alpha=0 outside —
    rgba_bg = _diagonal_gradient_rgba(
        "#0a0a0a", "#0a0a0a", W, H, angle_deg=0,
        card_x0=0.0, card_y0=0.0, card_x1=1.0, card_y1=1.0,
        corner_r=0.055,
    )
    bg_ax = fig.add_axes([0, 0, 1, 1])
    bg_ax.imshow(rgba_bg, aspect="auto", extent=[0, 1, 0, 1],
                 transform=bg_ax.transAxes, origin="upper")
    bg_ax.axis("off")

    # — Radial glow: position top:-40 right:-40, 180×180, rgba(255,107,53,0.3), blur(30px) —
    # Approximate: large low-opacity circle at top-right corner
    glow_ax = fig.add_axes([0, 0, 1, 1])
    glow_ax.axis("off")
    glow_ax.patch.set_alpha(0.0)
    for r, a in [(0.30, 0.04), (0.22, 0.07), (0.14, 0.10)]:
        glow_ax.add_patch(mpatches.Circle(
            (1.00, 1.00), r,
            facecolor="#ff6b35", edgecolor="none", alpha=a,
            transform=glow_ax.transAxes,
        ))

    if summary is not None:
        # — "MORNING RUN" label — 10px, weight:700, rgba(255,255,255,0.3) —
        fig.text(0.085, 0.835, "MORNING RUN",
                 color=(1, 1, 1, 0.30), ha="left", va="center",
                 fontsize=12, weight="bold")

        # — Distance hero — 64px, weight:800, white —
        # "km" suffix — 20px, weight:600, rgba(255,255,255,0.3)
        num_str = f"{summary.distance_km:.2f}"
        fig.text(0.085, 0.728, num_str,
                 color="#FFFFFF", ha="left", va="center",
                 fontproperties=_font_props("heavy", 80))
        # estimate offset: num ~4 chars × ~0.085 each
        dist_x_end = 0.085 + len(num_str) * 0.064
        fig.text(dist_x_end, 0.712, "km",
                 color=(1, 1, 1, 0.30), ha="left", va="center",
                 fontproperties=_font_props("semibold", 22))

        # — Mini route — top-right, 80×70 px equivalent —
        if activity.point_count >= 2:
            route_ax = fig.add_axes([0.63, 0.595, 0.295, 0.265])
            render_route(route_ax, activity,
                         RouteStyle(mode="solid", color="#ff6b35", line_width=2.5))

        # — Pace highlight bar — gradient(90deg, #ff6b35, #ff3366), borderRadius:12px —
        bar_img = _horiz_gradient_img("#ff6b35", "#ff3366", W=512)
        bar_ax = fig.add_axes([0.055, 0.425, 0.890, 0.160])
        bar_ax.set_xlim(0, 1)
        bar_ax.set_ylim(0, 1)
        bar_ax.axis("off")
        im = bar_ax.imshow(bar_img, aspect="auto", extent=[0, 1, 0, 1], origin="upper")
        clip = mpatches.FancyBboxPatch(
            (0.0, 0.0), 1.0, 1.0,
            boxstyle="round,pad=0.0,rounding_size=0.10",
            transform=bar_ax.transAxes,
            facecolor="none", edgecolor="none",
        )
        bar_ax.add_patch(clip)
        im.set_clip_path(clip)

        # Bar text: AVG PACE (left) — label 9px 60% white, value 26px weight:800
        fig.text(0.095, 0.533, "AVG PACE",
                 color=(1, 1, 1, 0.60), ha="left", va="center",
                 fontsize=11, weight="bold")
        fig.text(0.095, 0.472, _fmt_pace_apos(summary.avg_pace_min_per_km) + " /km",
                 color="#FFFFFF", ha="left", va="center",
                 fontproperties=_font_props("heavy", 34))

        # Bar text: DURATION (right) — label 9px 60% white, value 26px weight:800
        fig.text(0.905, 0.533, "DURATION",
                 color=(1, 1, 1, 0.60), ha="right", va="center",
                 fontsize=11, weight="bold")
        fig.text(0.905, 0.472, _fmt_duration_colon(summary.moving_time_s),
                 color="#FFFFFF", ha="right", va="center",
                 fontproperties=_font_props("heavy", 34))

        # — Bottom stats grid: 3 columns — label 9px 25% white, value 16px weight:700 —
        elev_str = (
            f"{summary.elevation_gain_m:+.0f}m"
            if summary.elevation_gain_m is not None else "N/A"
        )
        grid = [
            ("CALORIES",   _fmt_optional(summary.total_calories_kcal, " kcal")),
            ("HEART RATE", _fmt_optional(summary.avg_heart_rate_bpm, " bpm")),
            ("ELEVATION",  elev_str),
        ]
        xs = [0.22, 0.50, 0.78]
        for i, ((lbl, val), x) in enumerate(zip(grid, xs)):
            fig.text(x, 0.353, lbl,
                     color=(1, 1, 1, 0.25), ha="center", va="center",
                     fontsize=11, weight="bold")
            fig.text(x, 0.278, val,
                     color="#FFFFFF", ha="center", va="center",
                     fontproperties=_font_props("bold", 24))
            # border-left on columns 2 and 3: 1px solid rgba(255,255,255,0.06)
            if i > 0:
                div_x = (xs[i - 1] + x) / 2
                fig.lines.append(mlines.Line2D(
                    [div_x, div_x], [0.24, 0.39],
                    transform=fig.transFigure,
                    color="#FFFFFF", linewidth=1, alpha=0.06,
                ))

        # — Footer — date left, 10px, rgba(255,255,255,0.2) —
        date_str = _activity_date_str(activity)
        fig.text(0.085, 0.125, date_str,
                 color=(1, 1, 1, 0.20), ha="left", va="center",
                 fontsize=12, weight="medium")

    _save_figure(fig, output_path, style)

