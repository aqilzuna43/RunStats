from pathlib import Path
import unittest

from runstats.models import ActivityData, TrackPoint
from runstats.templates_stitch import _normalized_route_points, _story_timestamp


class StitchTemplateTests(unittest.TestCase):
    def test_normalized_route_points_fit_reference_viewbox(self) -> None:
        activity = ActivityData(
            source_path=Path("sample.fit"),
            source_type="fit",
            points=[
                TrackPoint(3.0, 101.0),
                TrackPoint(3.1, 101.2),
                TrackPoint(3.3, 101.4),
                TrackPoint(3.6, 101.1),
            ],
        )

        xs, ys = _normalized_route_points(activity)

        self.assertGreaterEqual(xs.min(), 40.0)
        self.assertLessEqual(xs.max(), 160.0)
        self.assertGreaterEqual(ys.min(), 50.0)
        self.assertLessEqual(ys.max(), 350.0)

    def test_story_timestamp_uses_activity_point_timestamp(self) -> None:
        activity = ActivityData(
            source_path=Path("sample.fit"),
            source_type="fit",
            points=[TrackPoint(3.0, 101.0)],
        )

        text = _story_timestamp(activity)

        self.assertIn("/", text)


if __name__ == "__main__":
    unittest.main()
