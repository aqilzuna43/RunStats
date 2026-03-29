from __future__ import annotations

import json
import tempfile
import unittest
from datetime import datetime, timezone
from pathlib import Path
from unittest.mock import patch

from runstats.automation import (
    build_ledger_key,
    build_telegram_caption,
    load_processed_ledger,
    run_automation,
    save_processed_ledger,
)
from runstats.metrics import SummaryError
from runstats.models import ActivityData, ActivitySummary, TrackPoint


class AutomationTests(unittest.TestCase):
    def test_build_telegram_caption_includes_location_when_present(self) -> None:
        summary = ActivitySummary(
            distance_km=5.0,
            moving_time_s=1500.0,
            elapsed_time_s=1500.0,
            avg_pace_min_per_km=5.0,
        )

        caption = build_telegram_caption(summary, "Eco Horizon, Penang")

        self.assertIn("5.00 km", caption)
        self.assertIn("25m 00s", caption)
        self.assertIn("5:00 /km", caption)
        self.assertTrue(caption.endswith("Eco Horizon, Penang"))

    def test_run_automation_renders_and_records_success(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "sample.fit"
            input_path.write_bytes(b"fit-bytes")
            activity = self._sample_activity(input_path)
            summary = self._sample_summary()

            def fake_render(*, output_path, **_kwargs) -> None:
                Path(output_path).write_bytes(b"png")

            with (
                patch("runstats.automation.load_activity", return_value=activity),
                patch("runstats.automation.summarize_activity", return_value=summary),
                patch("runstats.automation.reverse_geocode_activity", return_value="Eco Horizon, Penang"),
                patch("runstats.automation.render_template", side_effect=fake_render),
            ):
                result = run_automation(input_path=input_path, workspace_root=temp_path)

            self.assertEqual(result.status, "success")
            self.assertEqual(result.template, "glass_slab")
            self.assertTrue(Path(result.output_path).exists())
            self.assertEqual(result.location, "Eco Horizon, Penang")
            ledger = load_processed_ledger(temp_path / "logs" / "processed_ledger.json")
            self.assertIn(build_ledger_key(result.sha256, "glass_slab"), ledger)

            events = (temp_path / "logs" / "automation_events.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(len(events), 1)
            self.assertEqual(json.loads(events[0])["event"], "success")

    def test_run_automation_returns_duplicate_without_rendering(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "sample.fit"
            input_path.write_bytes(b"fit-bytes")
            workspace_logs = temp_path / "logs"
            workspace_logs.mkdir(parents=True, exist_ok=True)

            from runstats.automation import hash_file_sha256

            sha256 = hash_file_sha256(input_path)
            save_processed_ledger(
                workspace_logs / "processed_ledger.json",
                {
                    build_ledger_key(sha256, "glass_slab"): {
                        "template": "glass_slab",
                        "output_path": str(temp_path / "exports" / "glass_slab_sample.png"),
                        "distance_km": 5.0,
                        "moving_time_s": 1500.0,
                        "avg_pace_min_per_km": 5.0,
                        "location": "Eco Horizon, Penang",
                        "caption": "5.00 km | 25m 00s | 5:00 /km\nEco Horizon, Penang",
                    }
                },
            )

            with patch("runstats.automation.render_template") as render_mock:
                result = run_automation(input_path=input_path, workspace_root=temp_path)

            self.assertEqual(result.status, "duplicate")
            self.assertEqual(result.location, "Eco Horizon, Penang")
            render_mock.assert_not_called()

    def test_run_automation_allows_same_fit_for_different_templates(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "sample.fit"
            input_path.write_bytes(b"fit-bytes")
            activity = self._sample_activity(input_path)
            summary = self._sample_summary()

            def fake_render(*, output_path, **_kwargs) -> None:
                Path(output_path).write_bytes(b"png")

            with (
                patch("runstats.automation.load_activity", return_value=activity),
                patch("runstats.automation.summarize_activity", return_value=summary),
                patch("runstats.automation.render_template", side_effect=fake_render),
            ):
                first = run_automation(input_path=input_path, workspace_root=temp_path, template="glass_slab")
                second = run_automation(input_path=input_path, workspace_root=temp_path, template="clean_card")

            self.assertEqual(first.status, "success")
            self.assertEqual(second.status, "success")
            self.assertNotEqual(first.output_path, second.output_path)

    def test_run_automation_treats_geocode_failure_as_best_effort(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "sample.fit"
            input_path.write_bytes(b"fit-bytes")
            activity = self._sample_activity(input_path)
            summary = self._sample_summary()

            def fake_render(*, output_path, **_kwargs) -> None:
                Path(output_path).write_bytes(b"png")

            with (
                patch("runstats.automation.load_activity", return_value=activity),
                patch("runstats.automation.summarize_activity", return_value=summary),
                patch("runstats.automation.reverse_geocode_activity", side_effect=OSError("offline")),
                patch("runstats.automation.render_template", side_effect=fake_render),
            ):
                result = run_automation(input_path=input_path, workspace_root=temp_path)

            self.assertEqual(result.status, "success")
            self.assertIsNone(result.location)

    def test_run_automation_returns_error_payload_instead_of_raising(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            input_path = temp_path / "broken.fit"
            input_path.write_bytes(b"fit-bytes")

            with patch("runstats.automation.load_activity", side_effect=SummaryError("bad fit")):
                result = run_automation(input_path=input_path, workspace_root=temp_path)

            self.assertEqual(result.status, "error")
            self.assertIn("bad fit", result.error)
            events = (temp_path / "logs" / "automation_events.jsonl").read_text(encoding="utf-8").strip().splitlines()
            self.assertEqual(json.loads(events[0])["event"], "error")

    @staticmethod
    def _sample_activity(input_path: Path) -> ActivityData:
        start = datetime(2026, 3, 26, 6, 0, tzinfo=timezone.utc)
        return ActivityData(
            source_path=input_path,
            source_type="fit",
            points=[
                TrackPoint(5.2392, 100.4515, start, speed_mps=2.9),
                TrackPoint(5.2394, 100.4518, start, speed_mps=3.0),
            ],
        )

    @staticmethod
    def _sample_summary() -> ActivitySummary:
        return ActivitySummary(
            distance_km=5.0,
            moving_time_s=1500.0,
            elapsed_time_s=1500.0,
            avg_pace_min_per_km=5.0,
        )


if __name__ == "__main__":
    unittest.main()
