from __future__ import annotations

import math

from .models import ActivityData, ActivitySummary


EARTH_RADIUS_M = 6_371_000.0
MOVING_SPEED_THRESHOLD_MPS = 0.5


class SummaryError(ValueError):
    pass


def haversine_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)

    delta_lat = lat2_rad - lat1_rad
    delta_lon = lon2_rad - lon1_rad

    a = (
        math.sin(delta_lat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(delta_lon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_M * c


def summarize_activity(activity: ActivityData) -> ActivitySummary:
    points = activity.points
    if len(points) < 2:
        if activity.summary_hint is not None:
            return activity.summary_hint
        raise SummaryError("At least two track points are required.")

    distance_m = 0.0
    moving_time_s = 0.0
    elevation_gain_m = 0.0
    elevation_seen = False

    first_timestamp = points[0].timestamp
    last_timestamp = points[-1].timestamp
    if first_timestamp is None or last_timestamp is None:
        if activity.summary_hint is not None:
            return activity.summary_hint
        raise SummaryError(
            "Activity timestamps are missing. Re-run with --route-only for a route-only export."
        )

    for previous, current in zip(points, points[1:]):
        segment_distance = haversine_m(
            previous.latitude,
            previous.longitude,
            current.latitude,
            current.longitude,
        )
        distance_m += segment_distance

        if previous.elevation_m is not None and current.elevation_m is not None:
            elevation_seen = True
            gain = current.elevation_m - previous.elevation_m
            if gain > 0:
                elevation_gain_m += gain

        if previous.timestamp is None or current.timestamp is None:
            continue

        segment_time = (current.timestamp - previous.timestamp).total_seconds()
        if segment_time <= 0:
            continue

        measured_speed = current.speed_mps
        if measured_speed is None:
            measured_speed = segment_distance / segment_time if segment_time > 0 else 0.0

        if measured_speed >= MOVING_SPEED_THRESHOLD_MPS:
            moving_time_s += segment_time

    elapsed_time_s = (last_timestamp - first_timestamp).total_seconds()
    if elapsed_time_s <= 0 or distance_m <= 0:
        raise SummaryError("Activity timing or distance is invalid.")

    if moving_time_s <= 0:
        moving_time_s = elapsed_time_s

    distance_km = distance_m / 1000.0
    avg_pace_min_per_km = (moving_time_s / 60.0) / distance_km

    computed = ActivitySummary(
        distance_km=distance_km,
        moving_time_s=moving_time_s,
        elapsed_time_s=elapsed_time_s,
        avg_pace_min_per_km=avg_pace_min_per_km,
        elevation_gain_m=elevation_gain_m if elevation_seen else None,
    )
    return _merge_summary_hint(computed, activity.summary_hint)


def _merge_summary_hint(computed: ActivitySummary, hint: ActivitySummary | None) -> ActivitySummary:
    if hint is None:
        return computed

    return ActivitySummary(
        distance_km=computed.distance_km,
        moving_time_s=computed.moving_time_s,
        elapsed_time_s=computed.elapsed_time_s,
        avg_pace_min_per_km=computed.avg_pace_min_per_km,
        elevation_gain_m=computed.elevation_gain_m if computed.elevation_gain_m is not None else hint.elevation_gain_m,
        avg_heart_rate_bpm=hint.avg_heart_rate_bpm,
        total_calories_kcal=hint.total_calories_kcal,
    )


def format_distance_km(value: float) -> str:
    return f"{value:.2f} km"


def format_pace(value: float) -> str:
    total_seconds = int(round(value * 60))
    minutes, seconds = divmod(total_seconds, 60)
    return f"{minutes}:{seconds:02d} /km"


def format_duration(seconds: float) -> str:
    rounded = int(round(seconds))
    hours, remainder = divmod(rounded, 3600)
    minutes, secs = divmod(remainder, 60)

    if hours:
        return f"{hours}h {minutes:02d}m"
    if minutes:
        return f"{minutes}m {secs:02d}s"
    return f"{secs}s"
