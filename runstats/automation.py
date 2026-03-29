from __future__ import annotations

import argparse
import hashlib
import json
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import URLError

from .geocode import reverse_geocode_activity
from .ingest import load_activity
from .metrics import SummaryError, format_distance_km, format_duration, format_pace, summarize_activity
from .templates import DEFAULT_TITLE, TEMPLATE_NAMES, render_template


DEFAULT_AUTOMATION_TEMPLATE = "glass_slab"
DEFAULT_WORKSPACE_ROOT = Path(r"C:\RunStatsAutomation")
LEDGER_FILENAME = "processed_ledger.json"
EVENT_LOG_FILENAME = "automation_events.jsonl"


@dataclass(frozen=True)
class AutomationPaths:
    root: Path
    processing_dir: Path
    processed_dir: Path
    processed_duplicates_dir: Path
    failed_dir: Path
    failed_render_dir: Path
    failed_delivery_dir: Path
    exports_dir: Path
    logs_dir: Path
    ledger_path: Path
    events_log_path: Path


@dataclass(frozen=True)
class AutomationResult:
    status: str
    input_path: str
    sha256: str | None
    template: str
    output_path: str | None
    distance_km: float | None
    moving_time_s: float | None
    avg_pace_min_per_km: float | None
    location: str | None
    caption: str | None
    error: str | None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=True)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Render a machine-readable RunStats export for n8n and Telegram automation."
    )
    parser.add_argument("--input", required=True, help="Absolute path to the .fit or .gpx activity file.")
    parser.add_argument(
        "--template",
        default=DEFAULT_AUTOMATION_TEMPLATE,
        choices=TEMPLATE_NAMES,
        help="Template to render. Defaults to glass_slab for Telegram delivery.",
    )
    parser.add_argument(
        "--mode",
        default="auto",
        choices=("auto", "solid", "gradient"),
        help="Route rendering mode. 'auto' uses the template default.",
    )
    parser.add_argument(
        "--workspace",
        default=str(DEFAULT_WORKSPACE_ROOT),
        help="Automation workspace root used for exports, logs, and dedupe ledger.",
    )
    parser.add_argument("--output-dir", default=None, help="Optional override for the export output directory.")
    parser.add_argument("--ledger-path", default=None, help="Optional override for the processed ledger JSON file.")
    parser.add_argument("--events-log", default=None, help="Optional override for the JSONL event log.")
    parser.add_argument("--title", default=DEFAULT_TITLE, help="Optional title passed to the renderer.")
    parser.add_argument("--no-title", action="store_true", help="Hide the title text.")
    parser.add_argument("--location", default=None, help="Optional location label override.")
    parser.add_argument(
        "--no-geocode",
        action="store_true",
        help="Do not attempt reverse geocoding when --location is not provided.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    title = None if args.no_title else args.title

    result = run_automation(
        input_path=args.input,
        template=args.template,
        route_mode=args.mode,
        workspace_root=args.workspace,
        output_dir=args.output_dir,
        ledger_path=args.ledger_path,
        events_log_path=args.events_log,
        title=title,
        location=args.location,
        no_geocode=args.no_geocode,
    )
    print(result.to_json())
    return 0


def run_automation(
    *,
    input_path: str | Path,
    template: str = DEFAULT_AUTOMATION_TEMPLATE,
    route_mode: str = "auto",
    workspace_root: str | Path = DEFAULT_WORKSPACE_ROOT,
    output_dir: str | Path | None = None,
    ledger_path: str | Path | None = None,
    events_log_path: str | Path | None = None,
    title: str | None = DEFAULT_TITLE,
    location: str | None = None,
    no_geocode: bool = False,
) -> AutomationResult:
    input_file = Path(input_path).expanduser().resolve()
    paths = resolve_automation_paths(
        workspace_root=workspace_root,
        output_dir=output_dir,
        ledger_path=ledger_path,
        events_log_path=events_log_path,
    )
    ensure_workspace(paths)

    file_hash: str | None = None
    try:
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_file}")

        file_hash = hash_file_sha256(input_file)
        ledger = load_processed_ledger(paths.ledger_path)
        ledger_key = build_ledger_key(file_hash, template)
        existing = ledger.get(ledger_key)
        if existing is None:
            legacy = ledger.get(file_hash)
            if isinstance(legacy, dict) and str(legacy.get("template") or template) == template:
                existing = legacy
        if existing is not None:
            result = AutomationResult(
                status="duplicate",
                input_path=str(input_file),
                sha256=file_hash,
                template=str(existing.get("template") or template),
                output_path=_as_optional_str(existing.get("output_path")),
                distance_km=_as_optional_float(existing.get("distance_km")),
                moving_time_s=_as_optional_float(existing.get("moving_time_s")),
                avg_pace_min_per_km=_as_optional_float(existing.get("avg_pace_min_per_km")),
                location=_as_optional_str(existing.get("location")),
                caption=_as_optional_str(existing.get("caption")),
                error=None,
            )
            append_event(paths.events_log_path, "duplicate", result)
            return result

        activity = load_activity(input_file)
        summary = summarize_activity(activity)
        resolved_location = location
        if resolved_location is None and not no_geocode:
            resolved_location = safe_reverse_geocode(activity)

        resolved_mode = resolve_route_mode(route_mode, template, activity.has_speed_data())
        output_path = Path(paths.exports_dir) / f"{template}_{input_file.stem}.png"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        render_template(
            template_name=template,
            activity=activity,
            output_path=output_path,
            route_mode=resolved_mode,
            summary=summary,
            title=title,
            location=resolved_location,
        )

        caption = build_telegram_caption(summary, resolved_location)
        result = AutomationResult(
            status="success",
            input_path=str(input_file),
            sha256=file_hash,
            template=template,
            output_path=str(output_path),
            distance_km=summary.distance_km,
            moving_time_s=summary.moving_time_s,
            avg_pace_min_per_km=summary.avg_pace_min_per_km,
            location=resolved_location,
            caption=caption,
            error=None,
        )
        ledger[ledger_key] = {
            "processed_at": utc_now_iso(),
            "input_path": str(input_file),
            "template": template,
            "output_path": str(output_path),
            "distance_km": summary.distance_km,
            "moving_time_s": summary.moving_time_s,
            "avg_pace_min_per_km": summary.avg_pace_min_per_km,
            "location": resolved_location,
            "caption": caption,
        }
        save_processed_ledger(paths.ledger_path, ledger)
        append_event(paths.events_log_path, "success", result)
        return result
    except Exception as exc:
        result = AutomationResult(
            status="error",
            input_path=str(input_file),
            sha256=file_hash,
            template=template,
            output_path=None,
            distance_km=None,
            moving_time_s=None,
            avg_pace_min_per_km=None,
            location=location,
            caption=None,
            error=str(exc),
        )
        append_event(paths.events_log_path, "error", result)
        return result


def resolve_automation_paths(
    *,
    workspace_root: str | Path,
    output_dir: str | Path | None = None,
    ledger_path: str | Path | None = None,
    events_log_path: str | Path | None = None,
) -> AutomationPaths:
    root = Path(workspace_root).expanduser().resolve()
    logs_dir = root / "logs"
    resolved_output_dir = Path(output_dir).expanduser().resolve() if output_dir else root / "exports"
    resolved_ledger_path = Path(ledger_path).expanduser().resolve() if ledger_path else logs_dir / LEDGER_FILENAME
    resolved_events_log_path = (
        Path(events_log_path).expanduser().resolve() if events_log_path else logs_dir / EVENT_LOG_FILENAME
    )
    return AutomationPaths(
        root=root,
        processing_dir=root / "processing",
        processed_dir=root / "processed",
        processed_duplicates_dir=root / "processed" / "duplicates",
        failed_dir=root / "failed",
        failed_render_dir=root / "failed" / "render",
        failed_delivery_dir=root / "failed" / "delivery",
        exports_dir=resolved_output_dir,
        logs_dir=logs_dir,
        ledger_path=resolved_ledger_path,
        events_log_path=resolved_events_log_path,
    )


def ensure_workspace(paths: AutomationPaths) -> None:
    directories = (
        paths.root,
        paths.processing_dir,
        paths.processed_dir,
        paths.processed_duplicates_dir,
        paths.failed_dir,
        paths.failed_render_dir,
        paths.failed_delivery_dir,
        paths.exports_dir,
        paths.logs_dir,
        paths.ledger_path.parent,
        paths.events_log_path.parent,
    )
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)


def hash_file_sha256(path: str | Path) -> str:
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def load_processed_ledger(path: str | Path) -> dict[str, dict[str, object]]:
    ledger_path = Path(path)
    if not ledger_path.exists():
        return {}
    try:
        raw = json.loads(ledger_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    normalized: dict[str, dict[str, object]] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, dict):
            normalized[key] = dict(value)
    return normalized


def save_processed_ledger(path: str | Path, ledger: dict[str, dict[str, object]]) -> None:
    Path(path).write_text(json.dumps(ledger, indent=2, sort_keys=True), encoding="utf-8")


def append_event(path: str | Path, event_type: str, result: AutomationResult) -> None:
    record = {
        "timestamp": utc_now_iso(),
        "event": event_type,
        **asdict(result),
    }
    with Path(path).open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True))
        handle.write("\n")


def safe_reverse_geocode(activity) -> str | None:
    try:
        return reverse_geocode_activity(activity)
    except (OSError, URLError):
        return None


def resolve_route_mode(route_mode: str, template: str, has_speed_data: bool) -> str:
    if route_mode in {"solid", "gradient"}:
        if route_mode == "gradient" and not has_speed_data:
            return "solid"
        return route_mode
    if not has_speed_data:
        return "solid"
    return "gradient" if template == "clean_card" else "solid"


def build_telegram_caption(summary, location: str | None) -> str:
    caption = " | ".join(
        [
            format_distance_km(summary.distance_km),
            format_duration(summary.moving_time_s),
            format_pace(summary.avg_pace_min_per_km),
        ]
    )
    if location:
        return f"{caption}\n{location}"
    return caption


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def build_ledger_key(file_hash: str, template: str) -> str:
    return f"{file_hash}::{template}"


def _as_optional_str(value: object) -> str | None:
    return str(value) if isinstance(value, str) else None


def _as_optional_float(value: object) -> float | None:
    if isinstance(value, (int, float)):
        return float(value)
    return None


__all__ = [
    "AutomationPaths",
    "AutomationResult",
    "DEFAULT_AUTOMATION_TEMPLATE",
    "DEFAULT_WORKSPACE_ROOT",
    "build_parser",
    "build_ledger_key",
    "build_telegram_caption",
    "ensure_workspace",
    "hash_file_sha256",
    "load_processed_ledger",
    "main",
    "resolve_automation_paths",
    "resolve_route_mode",
    "run_automation",
    "save_processed_ledger",
]


if __name__ == "__main__":
    raise SystemExit(main())
