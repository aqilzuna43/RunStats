from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import cached_property
from pathlib import Path


@dataclass(frozen=True)
class TrackPoint:
    latitude: float
    longitude: float
    timestamp: datetime | None = None
    speed_mps: float | None = None
    elevation_m: float | None = None


@dataclass(frozen=True)
class ActivityData:
    source_path: Path
    source_type: str
    points: list[TrackPoint]
    summary_hint: "ActivitySummary | None" = None

    @property
    def point_count(self) -> int:
        return len(self.points)

    @cached_property
    def latitudes(self) -> tuple[float, ...]:
        return tuple(point.latitude for point in self.points)

    @cached_property
    def longitudes(self) -> tuple[float, ...]:
        return tuple(point.longitude for point in self.points)

    @cached_property
    def speeds_mps(self) -> tuple[float, ...]:
        return tuple(point.speed_mps or 0.0 for point in self.points)

    @cached_property
    def gradient_speeds(self) -> tuple[float, ...]:
        return tuple(speed for speed in self.speeds_mps if speed > 0.1)

    def has_speed_data(self) -> bool:
        return len(self.gradient_speeds) >= 10

    @cached_property
    def timestamp_count(self) -> int:
        return sum(1 for point in self.points if point.timestamp is not None)

    def has_timestamps(self) -> bool:
        return self.timestamp_count >= 2

    @cached_property
    def start_coordinate(self) -> tuple[float, float] | None:
        for point in self.points:
            return (point.latitude, point.longitude)
        return None


@dataclass(frozen=True)
class ActivitySummary:
    distance_km: float
    moving_time_s: float
    elapsed_time_s: float
    avg_pace_min_per_km: float
    elevation_gain_m: float | None = None
    avg_heart_rate_bpm: int | None = None
    total_calories_kcal: int | None = None
