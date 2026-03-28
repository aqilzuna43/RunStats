from pathlib import Path
import tempfile
import unittest

from runstats.geocode import _format_location_label, reverse_geocode
from runstats.models import ActivityData, TrackPoint


class GeocodeTests(unittest.TestCase):
    def test_format_location_prefers_locality_and_region(self) -> None:
        payload = {
            "address": {
                "suburb": "Eco Horizon",
                "state": "Penang",
                "country": "Malaysia",
            }
        }
        self.assertEqual(_format_location_label(payload), "Eco Horizon, Penang")

    def test_format_location_falls_back_when_only_city_exists(self) -> None:
        payload = {"address": {"city": "George Town"}}
        self.assertEqual(_format_location_label(payload), "George Town")

    def test_format_location_prefers_ascii_only_when_mixed_language(self) -> None:
        payload = {
            "address": {
                "suburb": "天域社区",
                "city": "Suzhou Industrial Park",
            }
        }
        self.assertEqual(_format_location_label(payload), "Suzhou Industrial Park")

    def test_reverse_geocode_uses_cache_without_network(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            cache_path = Path(temp_dir) / "cache.json"
            cache_path.write_text('{"5.23927,100.45155": "Eco Horizon, Penang"}', encoding="utf-8")
            self.assertEqual(reverse_geocode(5.23927127, 100.45154845, cache_path=cache_path), "Eco Horizon, Penang")

    def test_activity_start_coordinate_uses_first_point(self) -> None:
        activity = ActivityData(
            source_path=Path("sample.fit"),
            source_type="fit",
            points=[TrackPoint(5.1, 100.2), TrackPoint(5.2, 100.3)],
        )
        self.assertEqual(activity.start_coordinate, (5.1, 100.2))
