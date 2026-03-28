from __future__ import annotations

from pathlib import Path

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
    try:
        from fitparse import FitFile
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "FIT support requires 'fitparse'. Install the project dependencies first."
        ) from exc

    fit = FitFile(str(path))
    points: list[TrackPoint] = []
    session_summary: ActivitySummary | None = None

    for record in fit.get_messages("record"):
        lat = _field_value(record.fields, "position_lat")
        lon = _field_value(record.fields, "position_long")
        if lat is None or lon is None:
            continue

        points.append(
            _build_track_point(
                latitude=lat * SEMICIRCLE_TO_DEGREES,
                longitude=lon * SEMICIRCLE_TO_DEGREES,
                timestamp=_field_value(record.fields, "timestamp"),
                speed=_coalesce_fields(record.fields, "enhanced_speed", "speed"),
                elevation=_coalesce_fields(record.fields, "enhanced_altitude", "altitude"),
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
    try:
        import gpxpy
    except ModuleNotFoundError as exc:
        raise ModuleNotFoundError(
            "GPX support requires 'gpxpy'. Install the project dependencies first."
        ) from exc

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
                    _build_track_point(
                        latitude=point.latitude,
                        longitude=point.longitude,
                        timestamp=point.time,
                        speed=speed,
                        elevation=point.elevation,
                    )
                )

    for route in gpx.routes:
        for point in route.points:
            points.append(
                _build_track_point(
                    latitude=point.latitude,
                    longitude=point.longitude,
                    elevation=point.elevation,
                )
            )

    return ActivityData(source_path=path, source_type="gpx", points=points)


def _session_to_summary(session) -> ActivitySummary | None:
    total_distance_m = _field_value(session.fields, "total_distance")
    total_timer_time_s = _field_value(session.fields, "total_timer_time")
    total_elapsed_time_s = _field_value(session.fields, "total_elapsed_time")

    if total_distance_m in (None, 0) or total_timer_time_s in (None, 0):
        return None

    distance_km = float(total_distance_m) / 1000.0
    moving_time_s = float(total_timer_time_s)
    elapsed_time_s = float(total_elapsed_time_s or total_timer_time_s)
    avg_pace_min_per_km = (moving_time_s / 60.0) / distance_km

    elevation_gain = _field_value(session.fields, "total_ascent")
    avg_hr = _field_value(session.fields, "avg_heart_rate")
    calories = _field_value(session.fields, "total_calories")
    return ActivitySummary(
        distance_km=distance_km,
        moving_time_s=moving_time_s,
        elapsed_time_s=elapsed_time_s,
        avg_pace_min_per_km=avg_pace_min_per_km,
        elevation_gain_m=float(elevation_gain) if elevation_gain is not None else None,
        avg_heart_rate_bpm=int(avg_hr) if avg_hr is not None else None,
        total_calories_kcal=int(calories) if calories is not None else None,
    )


def _build_track_point(
    *,
    latitude: float,
    longitude: float,
    timestamp=None,
    speed=None,
    elevation=None,
) -> TrackPoint:
    return TrackPoint(
        latitude=latitude,
        longitude=longitude,
        timestamp=timestamp,
        speed_mps=float(speed) if speed is not None else None,
        elevation_m=float(elevation) if elevation is not None else None,
    )


def _field_value(fields, name: str):
    for field in fields:
        if field.name == name:
            return field.value
    return None


def _coalesce_fields(fields, *names: str):
    for name in names:
        value = _field_value(fields, name)
        if value is not None:
            return value
    return None
