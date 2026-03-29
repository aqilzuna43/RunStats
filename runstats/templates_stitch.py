from __future__ import annotations

import math
import shutil
import subprocess
import tempfile
from datetime import datetime
from pathlib import Path
from urllib.parse import quote

import numpy as np

from .models import ActivityData, ActivitySummary
from .template_support import fmt_duration_colon, fmt_pace_apos

_REFERENCE_DIR = Path(__file__).resolve().parent / "neon-data-story"
_REFERENCE_HTML = _REFERENCE_DIR / "code.html"

_EDGE_CANDIDATES = (
    Path(r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"),
    Path(r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"),
    Path(r"C:\Program Files\Google\Chrome\Application\chrome.exe"),
)

_CANVAS_WIDTH = 1080
_CANVAS_HEIGHT = 1920
_BASE_WIDTH = 497
_BASE_HEIGHT = 884
_SCALE = _CANVAS_HEIGHT / _BASE_HEIGHT


def render_neon_data_story(
    activity: ActivityData,
    output_path: str | Path,
    route_mode: str,
    summary: ActivitySummary | None,
    location: str | None = None,
) -> None:
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)

    html = _build_story_html(activity, summary, location)
    browser = _resolve_browser()

    with tempfile.TemporaryDirectory(prefix="runstats-neon-story-") as temp_dir_str:
        temp_dir = Path(temp_dir_str)
        html_path = temp_dir / "story.html"
        profile_dir = temp_dir / "browser-profile"
        profile_dir.mkdir(parents=True, exist_ok=True)
        html_path.write_text(html, encoding="utf-8")

        url = html_path.resolve().as_uri()
        command = [
            str(browser),
            "--headless",
            "--disable-gpu",
            "--hide-scrollbars",
            "--no-first-run",
            "--no-default-browser-check",
            f"--user-data-dir={profile_dir}",
            f"--window-size={_CANVAS_WIDTH},{_CANVAS_HEIGHT}",
            "--force-device-scale-factor=1",
            "--virtual-time-budget=5000",
            f"--screenshot={output.resolve()}",
            url,
        ]
        result = subprocess.run(command, capture_output=True, text=True, check=False)
        if result.returncode != 0 or not output.exists():
            stderr = (result.stderr or "").strip()
            raise RuntimeError(
                "Failed to render neon_data_story HTML template via headless browser."
                + (f" Browser output: {stderr}" if stderr else "")
            )


def _build_story_html(
    activity: ActivityData,
    summary: ActivitySummary | None,
    location: str | None,
) -> str:
    template = _REFERENCE_HTML.read_text(encoding="utf-8")

    location_text = (location or "RUN LOCATION").upper()
    timestamp_text = _story_timestamp(activity)
    distance_text = f"{summary.distance_km:.2f}" if summary is not None else "0.00"
    pace_text = _pace_text(summary)
    time_text = fmt_duration_colon(summary.moving_time_s) if summary is not None else "00:00"
    elevation_text = _elevation_text(summary)
    athlete_text = "RUNSTATS ATHLETE"
    route_path = _route_svg_path(activity)
    start_x, start_y, end_x, end_y = _route_endpoints(activity)

    replacements = {
        ">LOS ANGELES, CA<": f">{_escape_html(location_text)}<",
        ">MAY 24 / 06:42 AM<": f">{_escape_html(timestamp_text)}<",
        ">10.50<": f">{_escape_html(distance_text)}<",
        ">05:30<": f">{_escape_html(pace_text)}<",
        ">57:45<": f">{_escape_html(time_text)}<",
        ">342 M<": f">{_escape_html(elevation_text)}<",
        ">ELARA VANCE<": f">{_escape_html(athlete_text)}<",
        'd="M100 350 L80 300 L120 250 L40 180 L160 120 L100 50"': f'd="{route_path}"',
        'cx="100" cy="50" fill="#f3ffca" r="4"': f'cx="{end_x:.1f}" cy="{end_y:.1f}" fill="#f3ffca" r="4"',
        'cx="100" cy="50" fill="#f3ffca" opacity="0.3" r="8"': (
            f'cx="{end_x:.1f}" cy="{end_y:.1f}" fill="#f3ffca" opacity="0.3" r="8"'
        ),
    }
    for old, new in replacements.items():
        template = template.replace(old, new)

    # Remove the athlete portrait dependency so the footer stays stable even if the remote image changes.
    template = template.replace(
        '<img class="w-full h-full object-cover" data-alt="portrait of a focused female athlete with sweat on skin, dramatic lighting" src="https://lh3.googleusercontent.com/aida-public/AB6AXuAWHKOhWBVlf44zMEzB_nMaXKAyzHLgu_YEFASlxyf0iIlXtaq5Y243DShD9Lb8-7ZFJ0D3fczNbCe9qscKPxdkBHYhodjBPW84YhIZm7eNOiv9iEY3dVtx_mFSMYgrL-A9_FL1v2mm1OWJffgEvhF0mD9IFGfa9RS8k8qlztBk8ex1RSGfbMSmx2FkyTtUikxXE9rag2WHY3AO9SMk1M3ZXRYVnfNzBPnE05wkhp4nXx8tJtX1eftNH7ffAhhhW19WIAVIOhwb0DAD"/>',
        '<div class="w-full h-full bg-gradient-to-br from-primary/40 to-transparent"></div>',
    )

    return _wrap_for_instagram_story(template)


def _wrap_for_instagram_story(html: str) -> str:
    body_open = '<body class="bg-black text-on-surface font-body overflow-hidden">'
    body_replacement = (
        '<body class="bg-black text-on-surface font-body overflow-hidden" '
        'style="margin:0;width:1080px;height:1920px;overflow:hidden;background:#000000;">'
        f'<div style="width:{_CANVAS_WIDTH}px;height:{_CANVAS_HEIGHT}px;overflow:hidden;background:#000000;">'
        f'<div style="width:{_BASE_WIDTH}px;height:{_BASE_HEIGHT}px;transform-origin:top left;transform:scale({_SCALE:.8f});">'
    )
    html = html.replace(body_open, body_replacement, 1)
    html = html.replace("</body>", "</div></div></body>", 1)
    return html


def _story_timestamp(activity: ActivityData) -> str:
    for point in activity.points:
        if point.timestamp is not None:
            stamp = point.timestamp
            return stamp.strftime("%b %d / %I:%M %p").upper()
    return datetime.today().strftime("%b %d / %I:%M %p").upper()


def _pace_text(summary: ActivitySummary | None) -> str:
    if summary is None:
        return "00:00"
    pace = fmt_pace_apos(summary.avg_pace_min_per_km)
    return pace.replace("'", ":").replace('"', "")


def _elevation_text(summary: ActivitySummary | None) -> str:
    if summary is None or summary.elevation_gain_m is None:
        return "N/A"
    return f"{int(round(summary.elevation_gain_m))} M"


def _route_svg_path(activity: ActivityData) -> str:
    xs, ys = _normalized_route_points(activity)
    commands = [f"M{xs[0]:.1f} {ys[0]:.1f}"]
    commands.extend(f"L{x:.1f} {y:.1f}" for x, y in zip(xs[1:], ys[1:]))
    return " ".join(commands)


def _route_endpoints(activity: ActivityData) -> tuple[float, float, float, float]:
    xs, ys = _normalized_route_points(activity)
    return xs[0], ys[0], xs[-1], ys[-1]


def _normalized_route_points(activity: ActivityData) -> tuple[np.ndarray, np.ndarray]:
    if activity.point_count < 2:
        return np.array([100.0, 100.0]), np.array([350.0, 50.0])

    points = np.column_stack((np.array(activity.longitudes), np.array(activity.latitudes)))

    sample_limit = 90
    if len(points) > sample_limit:
        indices = np.linspace(0, len(points) - 1, sample_limit).round().astype(int)
        points = points[indices]

    centered = points - points.mean(axis=0)
    covariance = np.cov(centered.T)
    eigenvalues, eigenvectors = np.linalg.eigh(covariance)
    principal = eigenvectors[:, np.argmax(eigenvalues)]
    angle = math.atan2(principal[1], principal[0])
    rotation = (math.pi / 2) - angle
    rotation_matrix = np.array(
        [
            [math.cos(rotation), -math.sin(rotation)],
            [math.sin(rotation), math.cos(rotation)],
        ]
    )
    rotated = centered @ rotation_matrix.T

    # Ensure the route "current position" sits near the top like the Stitch reference.
    if rotated[-1, 1] < rotated[0, 1]:
        rotated[:, 1] *= -1

    x = rotated[:, 0]
    y = rotated[:, 1]
    if len(x) >= 5:
        kernel = np.array([1.0, 2.0, 3.0, 2.0, 1.0], dtype=float)
        kernel /= kernel.sum()
        x = np.convolve(x, kernel, mode="same")
        y = np.convolve(y, kernel, mode="same")
    x -= x.min()
    y -= y.min()

    x_span = max(x.max(), 1e-9)
    y_span = max(y.max(), 1e-9)

    target_x0, target_x1 = 58.0, 142.0
    target_y0, target_y1 = 78.0, 285.0

    x = target_x0 + (x / x_span) * (target_x1 - target_x0)
    y = target_y1 - (y / y_span) * (target_y1 - target_y0)

    return x, y


def _resolve_browser() -> Path:
    edge = shutil.which("msedge")
    chrome = shutil.which("chrome")
    if edge:
        return Path(edge)
    if chrome:
        return Path(chrome)
    for candidate in _EDGE_CANDIDATES:
        if candidate.exists():
            return candidate
    raise RuntimeError(
        "No supported Chromium browser found. Install Microsoft Edge or Google Chrome to render neon_data_story."
    )


def _escape_html(value: str) -> str:
    return (
        value.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )
