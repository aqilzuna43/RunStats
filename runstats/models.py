from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
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
    def latitudes(self) -> list[float]:
        return [point.latitude for point in self.points]

    @property
    def longitudes(self) -> list[float]:
        return [point.longitude for point in self.points]

    @property
    def speeds_mps(self) -> list[float]:
        return [point.speed_mps or 0.0 for point in self.points]

    def has_speed_data(self) -> bool:
        return len([speed for speed in self.speeds_mps if speed > 0.1]) >= 10

    def has_timestamps(self) -> bool:
        return sum(1 for point in self.points if point.timestamp is not None) >= 2


@dataclass(frozen=True)
class ActivitySummary:
    distance_km: float
    moving_time_s: float
    elapsed_time_s: float
    avg_pace_min_per_km: float
    elevation_gain_m: float | None = None
