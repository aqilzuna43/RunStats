from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .ingest import discover_activity_files, load_activity
from .metrics import SummaryError, summarize_activity
from .templates import DEFAULT_TITLE, TEMPLATE_NAMES, render_template


_TEMPLATE_LABELS = [
    ("story_overlay", "Story Overlay - 1080x1920 Instagram story"),
    ("clean_card", "Clean Card - 1600x1600 square card"),
    ("glass_slab", "Glass Slab - Frosted glass with map peek-through"),
    ("clipboard_card", "Clipboard Card - Stacked stat rows, orange accent"),
    ("neon_split", "Neon Split - Dark card with gradient accent bar"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Render route-based run stat overlays from FIT or GPX files.")
    parser.add_argument("--input", help="Path to a .fit or .gpx activity file.")
    parser.add_argument("--output", help="Output PNG path.")
    parser.add_argument(
        "--template",
        default="story_overlay",
        choices=TEMPLATE_NAMES,
        help="Template to render.",
    )
    parser.add_argument(
        "--mode",
        default="auto",
        choices=("auto", "solid", "gradient"),
        help="Route rendering mode. 'auto' uses the template default.",
    )
    parser.add_argument("--title", default=DEFAULT_TITLE, help="Optional title shown near the bottom of the export.")
    parser.add_argument("--no-title", action="store_true", help="Hide the title text.")
    parser.add_argument("--auto", action="store_true", help="Skip prompts and auto-select the most recent activity file.")
    parser.add_argument(
        "--search-dir",
        default=".",
        help="Directory to scan for .fit and .gpx files when --input is not set.",
    )
    parser.add_argument(
        "--route-only",
        action="store_true",
        help="Render without summary stats if timing data is unavailable.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    input_path = _resolve_input(args.input, args.search_dir, args.auto)
    activity = load_activity(input_path)

    summary = None
    try:
        summary = summarize_activity(activity)
    except SummaryError as exc:
        if not args.route_only:
            print(str(exc), file=sys.stderr)
            print("Re-run with --route-only to export a route-only template.", file=sys.stderr)
            return 1
        print(f"Summary unavailable: {exc}", file=sys.stderr)

    if activity.point_count < 2 and summary is None:
        print("No usable route points found in the selected activity file.", file=sys.stderr)
        return 1
    if args.route_only and activity.point_count < 2:
        print("Route-only export requires at least two route points.", file=sys.stderr)
        return 1

    template = _resolve_template(args.template, args.auto)
    route_mode = _resolve_route_mode(args.mode, template, activity.has_speed_data(), args.auto)
    title = None if args.no_title else args.title
    output_path = Path(args.output) if args.output else Path(f"{template}.png")

    print(f"Selected: {Path(input_path).name}")
    print(f"Template: {template}")
    print(f"Mode: {route_mode}")
    print(f"Points: {activity.point_count}")
    if summary is not None:
        print(f"Distance: {summary.distance_km:.2f} km")
        print(f"Pace: {summary.avg_pace_min_per_km:.2f} min/km")
        print(f"Time: {summary.moving_time_s / 60.0:.1f} min")

    render_template(
        template_name=template,
        activity=activity,
        output_path=output_path,
        route_mode=route_mode,
        summary=summary,
        title=title,
    )
    print(f"Saved to {output_path}")
    return 0


def _resolve_input(explicit_input: str | None, search_dir: str, auto_select: bool) -> Path:
    if explicit_input:
        return Path(explicit_input)

    files = discover_activity_files(search_dir)
    if not files:
        raise SystemExit("No .fit or .gpx files found.")

    if len(files) == 1:
        print(f"Auto-selected: {files[0].name}")
        return files[0]

    if auto_select or not sys.stdin.isatty():
        chosen = max(files, key=lambda path: path.stat().st_mtime)
        print(f"Auto-selected most recent file: {chosen.name}")
        return chosen

    print("\n--- Available activity files ---")
    for index, path in enumerate(files, start=1):
        size_kb = path.stat().st_size / 1024
        print(f"  [{index}] {path.name} ({path.suffix.lstrip('.').upper()}, {size_kb:.0f} KB)")

    while True:
        choice = input(f"Select file [1-{len(files)}]: ").strip()
        if choice.isdigit() and 1 <= int(choice) <= len(files):
            return files[int(choice) - 1]
        print(f"Invalid choice. Enter a number between 1 and {len(files)}.")


def _resolve_template(explicit: str, auto_select: bool) -> str:
    if explicit != "story_overlay":
        return explicit
    if auto_select or not sys.stdin.isatty():
        return explicit

    print("\n--- Overlay templates ---")
    for index, (_, desc) in enumerate(_TEMPLATE_LABELS, start=1):
        print(f"  [{index}] {desc}")

    while True:
        choice = input(f"Select template [1-{len(_TEMPLATE_LABELS)}] (default 1): ").strip()
        if choice == "":
            return _TEMPLATE_LABELS[0][0]
        if choice.isdigit() and 1 <= int(choice) <= len(_TEMPLATE_LABELS):
            return _TEMPLATE_LABELS[int(choice) - 1][0]
        print(f"Invalid choice. Enter a number between 1 and {len(_TEMPLATE_LABELS)}.")


def _resolve_route_mode(mode: str, template: str, has_speed_data: bool, auto_select: bool) -> str:
    if mode in {"solid", "gradient"}:
        if mode == "gradient" and not has_speed_data:
            print("Speed data unavailable; falling back to solid mode.")
            return "solid"
        return mode

    default_mode = "gradient" if template == "clean_card" else "solid"
    if not has_speed_data:
        return "solid"

    if auto_select or not sys.stdin.isatty():
        return default_mode

    print()
    print("Render mode options:")
    print("  [1] Solid orange")
    print("  [2] Speed gradient")
    recommended = "1" if default_mode == "solid" else "2"

    while True:
        choice = input(f"Render mode [1/2] (default {recommended}): ").strip()
        if choice == "":
            choice = recommended
        if choice == "1":
            return "solid"
        if choice == "2":
            return "gradient"
        print("Enter 1 or 2.")
