from __future__ import annotations

from pathlib import Path

import gpxpy

from .models import ActivityData, ActivitySummary, TrackPoint


SEMICIRCLE_TO_DEGREES = 180.0 / (2**31)
SUPPORTED_EXTENSIONS = {".fit", ".gpx"}


def discover_activity_files(search_dir: str | Path) -> list[Path]:
    base = Path(search_dir)
    files: list[Path] = []
    for ext in sorted(SUPPORTED_EXTENSIONS):
        files.extend(sorted(base.glob(f"*{ext}")))
    return files


def load_activity(path: str | Path) -> ActivityData:
    activity_path = Path(path)
    suffix = activity_path.suffix.lower()

    if suffix == ".fit":
        return _parse_fit(activity_path)
    if suffix == ".gpx":
        return _parse_gpx(activity_path)

    raise ValueError(f"Unsupported file type: {suffix}")


def _parse_fit(path: Path) -> ActivityData:
    from fitparse import FitFile

    fit = FitFile(str(path))
    points: list[TrackPoint] = []
    session_summary: ActivitySummary | None = None

    for record in fit.get_messages("record"):
        data = {field.name: field.value for field in record.fields}

        lat = data.get("position_lat")
        lon = data.get("position_long")
        if lat is None or lon is None:
            continue

        speed = data.get("enhanced_speed")
        if speed is None:
            speed = data.get("speed")

        elevation = data.get("enhanced_altitude")
        if elevation is None:
            elevation = data.get("altitude")

        points.append(
            TrackPoint(
                latitude=lat * SEMICIRCLE_TO_DEGREES,
                longitude=lon * SEMICIRCLE_TO_DEGREES,
                timestamp=data.get("timestamp"),
                speed_mps=float(speed) if speed is not None else None,
                elevation_m=float(elevation) if elevation is not None else None,
            )
        )

    for session in fit.get_messages("session"):
        session_summary = _session_to_summary(session)
        if session_summary is not None:
            break

    return ActivityData(
        source_path=path,
        source_type="fit",
        points=points,
        summary_hint=session_summary,
    )


def _parse_gpx(path: Path) -> ActivityData:
    with path.open("r", encoding="utf-8") as handle:
        gpx = gpxpy.parse(handle)

    points: list[TrackPoint] = []

    for track in gpx.tracks:
        for segment in track.segments:
            segment_points = segment.points
            for index, point in enumerate(segment_points):
                speed = point.speed
                if speed is None and index > 0:
                    speed = point.speed_between(segment_points[index - 1]) or None

                points.append(
                    TrackPoint(
                        latitude=point.latitude,
                        longitude=point.longitude,
                        timestamp=point.time,
                        speed_mps=float(speed) if speed is not None else None,
                        elevation_m=float(point.elevation) if point.elevation is not None else None,
                    )
                )

    for route in gpx.routes:
        for point in route.points:
            points.append(
                TrackPoint(
                    latitude=point.latitude,
                    longitude=point.longitude,
                    elevation_m=float(point.elevation) if point.elevation is not None else None,
                )
            )

    return ActivityData(source_path=path, source_type="gpx", points=points)


def _session_to_summary(session) -> ActivitySummary | None:
    data = {field.name: field.value for field in session.fields}
    total_distance_m = data.get("total_distance")
    total_timer_time_s = data.get("total_timer_time")
    total_elapsed_time_s = data.get("total_elapsed_time")

    if total_distance_m in (None, 0) or total_timer_time_s in (None, 0):
        return None

    distance_km = float(total_distance_m) / 1000.0
    moving_time_s = float(total_timer_time_s)
    elapsed_time_s = float(total_elapsed_time_s or total_timer_time_s)
    avg_pace_min_per_km = (moving_time_s / 60.0) / distance_km

    elevation_gain = data.get("total_ascent")
    return ActivitySummary(
        distance_km=distance_km,
        moving_time_s=moving_time_s,
        elapsed_time_s=elapsed_time_s,
        avg_pace_min_per_km=avg_pace_min_per_km,
        elevation_gain_m=float(elevation_gain) if elevation_gain is not None else None,
    )
