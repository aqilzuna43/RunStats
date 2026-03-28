from datetime import datetime, timedelta, timezone
from pathlib import Path
import unittest

from runstats.metrics import SummaryError, format_duration, format_pace, haversine_m, summarize_activity
from runstats.models import ActivityData, ActivitySummary, TrackPoint


class MetricsTests(unittest.TestCase):
    def test_haversine_returns_positive_distance(self) -> None:
        distance = haversine_m(3.139, 101.6869, 3.14, 101.6879)
        self.assertGreater(distance, 100.0)

    def test_format_duration(self) -> None:
        self.assertEqual(format_duration(7140), "1h 59m")

    def test_format_pace(self) -> None:
        self.assertEqual(format_pace(6 + 58 / 60), "6:58 /km")

    def test_summarize_activity(self) -> None:
        start = datetime(2026, 3, 26, 6, 0, tzinfo=timezone.utc)
        points = [
            TrackPoint(3.1390, 101.6869, start),
            TrackPoint(3.1399, 101.6879, start + timedelta(minutes=5)),
            TrackPoint(3.1408, 101.6889, start + timedelta(minutes=10)),
        ]
        activity = ActivityData(source_path=Path("sample.gpx"), source_type="gpx", points=points)
        summary = summarize_activity(activity)

        self.assertGreater(summary.distance_km, 0.2)
        self.assertAlmostEqual(summary.elapsed_time_s, 600.0)

    def test_summarize_requires_two_points(self) -> None:
        activity = ActivityData(
            source_path=Path("sample.gpx"),
            source_type="gpx",
            points=[TrackPoint(3.1390, 101.6869)],
        )
        with self.assertRaises(SummaryError):
            summarize_activity(activity)

    def test_summarize_uses_summary_hint_without_timestamps(self) -> None:
        summary_hint = ActivitySummary(
            distance_km=5.0,
            moving_time_s=1500.0,
            elapsed_time_s=1500.0,
            avg_pace_min_per_km=5.0,
        )
        activity = ActivityData(
            source_path=Path("sample.gpx"),
            source_type="gpx",
            points=[
                TrackPoint(3.1390, 101.6869),
                TrackPoint(3.1399, 101.6879),
            ],
            summary_hint=summary_hint,
        )

        self.assertIs(summarize_activity(activity), summary_hint)

    def test_activity_data_caches_derived_sequences(self) -> None:
        points = [
            TrackPoint(3.1390 + index * 0.0001, 101.6869 + index * 0.0001, speed_mps=1.5)
            for index in range(12)
        ]
        activity = ActivityData(source_path=Path("sample.gpx"), source_type="gpx", points=points)

        self.assertEqual(activity.point_count, 12)
        self.assertIs(activity.latitudes, activity.latitudes)
        self.assertIs(activity.longitudes, activity.longitudes)
        self.assertIs(activity.speeds_mps, activity.speeds_mps)
        self.assertTrue(activity.has_speed_data())


if __name__ == "__main__":
    unittest.main()
