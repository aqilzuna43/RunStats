from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from runstats.automation import resolve_automation_paths
from runstats.telegram_bot import (
    IncomingDocument,
    TelegramBotConfig,
    build_multipart_body,
    build_template_prompt,
    extract_document,
    handle_update,
    load_offset,
    load_pending_requests,
    resolve_template_choice,
    sanitize_filename,
    save_offset,
    unique_processing_path,
)


class FakeTelegramClient:
    def __init__(self) -> None:
        self.messages: list[tuple[int, str]] = []
        self.documents: list[tuple[int, str, str | None]] = []
        self.file_path = "documents/file.fit"
        self.download_payload = b"fit-data"

    def get_file_path(self, file_id: str) -> str:
        return self.file_path

    def download_file(self, file_path: str) -> bytes:
        return self.download_payload

    def send_message(self, chat_id: int, text: str, **_kwargs):
        self.messages.append((chat_id, text))
        return {"ok": True}

    def send_document(self, chat_id: int, document_path: str | Path, caption: str | None = None, **_kwargs):
        self.documents.append((chat_id, str(document_path), caption))
        return {"ok": True}


class TelegramBotTests(unittest.TestCase):
    def test_extract_document_returns_fit_metadata(self) -> None:
        update = {
            "update_id": 42,
            "message": {
                "message_id": 7,
                "chat": {"id": 535004713},
                "document": {"file_id": "abc123", "file_name": "run.fit", "mime_type": "application/octet-stream"},
            },
        }

        incoming = extract_document(update)

        self.assertEqual(
            incoming,
            IncomingDocument(
                update_id=42,
                chat_id=535004713,
                message_id=7,
                file_id="abc123",
                file_name="run.fit",
                mime_type="application/octet-stream",
            ),
        )

    def test_sanitize_filename_replaces_windows_unsafe_characters(self) -> None:
        self.assertEqual(sanitize_filename('bad<>:"/\\\\|?*\u0000.fit'), "bad___________.fit")

    def test_unique_processing_path_appends_update_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            path = unique_processing_path(temp_dir, "20377609259_ACTIVITY.fit", 99)
            self.assertEqual(path.name, "20377609259_ACTIVITY_99.fit")

    def test_resolve_template_choice_accepts_number_and_name(self) -> None:
        self.assertEqual(resolve_template_choice("1"), "story_overlay")
        self.assertEqual(resolve_template_choice("glass_slab"), "glass_slab")

    def test_offset_round_trip(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            offset_path = Path(temp_dir) / "offset.txt"
            save_offset(offset_path, 123)
            self.assertEqual(load_offset(offset_path), 123)

    def test_fit_upload_queues_pending_request_and_prompts_for_template(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = resolve_automation_paths(workspace_root=temp_dir)
            client = FakeTelegramClient()

            handle_update(update=self._fit_update(), config=self._config(temp_dir), client=client, paths=paths)

            self.assertEqual(client.messages, [(535004713, build_template_prompt())])
            pending = load_pending_requests(Path(temp_dir) / "logs" / "telegram_pending_requests.json")
            self.assertIn("535004713", pending)

    def test_handle_update_rejects_non_fit_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = resolve_automation_paths(workspace_root=temp_dir)
            client = FakeTelegramClient()

            update = {
                "update_id": 1,
                "message": {
                    "message_id": 1,
                    "chat": {"id": 535004713},
                    "document": {"file_id": "abc123", "file_name": "photo.jpg"},
                },
            }

            handle_update(update=update, config=self._config(temp_dir), client=client, paths=paths)

            self.assertEqual(client.messages, [(535004713, "Send a .FIT document to this bot to start processing.")])

    def test_template_reply_success_sends_document_and_archives_fit(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = resolve_automation_paths(workspace_root=temp_dir)
            client = FakeTelegramClient()
            self._queue_pending_fit(temp_dir, client, paths)

            result = self._result(
                status="success",
                output_path=str(Path(temp_dir) / "exports" / "glass_slab.png"),
                caption="5.00 km | 25m 00s | 5:00 /km",
            )
            Path(result.output_path).parent.mkdir(parents=True, exist_ok=True)
            Path(result.output_path).write_bytes(b"png")

            with patch("runstats.telegram_bot.run_automation", return_value=result) as automation_mock:
                handle_update(update=self._text_update("glass_slab"), config=self._config(temp_dir), client=client, paths=paths)

            self.assertEqual(len(client.documents), 1)
            self.assertEqual(automation_mock.call_args.kwargs["template"], "glass_slab")
            archived = list((Path(temp_dir) / "processed").glob("*.fit"))
            self.assertEqual(len(archived), 1)

    def test_template_reply_duplicate_sends_message_and_archives_duplicate(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = resolve_automation_paths(workspace_root=temp_dir)
            client = FakeTelegramClient()
            self._queue_pending_fit(temp_dir, client, paths)

            with patch("runstats.telegram_bot.run_automation", return_value=self._result(status="duplicate")):
                handle_update(update=self._text_update("glass_slab"), config=self._config(temp_dir), client=client, paths=paths)

            self.assertIn((535004713, "This FIT activity was already processed for that template."), client.messages)
            archived = list((Path(temp_dir) / "processed" / "duplicates").glob("*.fit"))
            self.assertEqual(len(archived), 1)

    def test_template_reply_error_sends_message_and_archives_failed_render(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = resolve_automation_paths(workspace_root=temp_dir)
            client = FakeTelegramClient()
            self._queue_pending_fit(temp_dir, client, paths)

            with patch(
                "runstats.telegram_bot.run_automation",
                return_value=self._result(status="error", error="bad fit"),
            ):
                handle_update(update=self._text_update("glass_slab"), config=self._config(temp_dir), client=client, paths=paths)

            self.assertIn((535004713, "RunStats could not render this FIT file. bad fit"), client.messages)
            archived = list((Path(temp_dir) / "failed" / "render").glob("*.fit"))
            self.assertEqual(len(archived), 1)

    def test_invalid_template_reply_prompts_again(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            paths = resolve_automation_paths(workspace_root=temp_dir)
            client = FakeTelegramClient()
            self._queue_pending_fit(temp_dir, client, paths)

            handle_update(update=self._text_update("not-a-template"), config=self._config(temp_dir), client=client, paths=paths)

            self.assertIn((535004713, "Pick one of the template names below after sending your FIT file."), client.messages)

    def test_build_multipart_body_contains_file_and_fields(self) -> None:
        body = build_multipart_body(
            fields={"chat_id": "535004713"},
            files={"document": ("result.png", b"png", "image/png")},
            boundary="test-boundary",
        )

        text = body.decode("utf-8", errors="ignore")
        self.assertIn('name="chat_id"', text)
        self.assertIn('filename="result.png"', text)
        self.assertIn("image/png", text)

    def _config(self, temp_dir: str) -> TelegramBotConfig:
        return TelegramBotConfig(
            token="token",
            workspace_root=Path(temp_dir),
            template="glass_slab",
            route_mode="auto",
            allowed_chat_id=535004713,
            title=None,
            location=None,
            no_geocode=False,
            poll_timeout_s=30,
            request_timeout_s=60,
            retry_delay_s=1,
            once=True,
            offset_path=Path(temp_dir) / "logs" / "offset.txt",
        )

    @staticmethod
    def _fit_update() -> dict:
        return {
            "update_id": 3,
            "message": {
                "message_id": 3,
                "chat": {"id": 535004713},
                "document": {"file_id": "abc123", "file_name": "20377609259_ACTIVITY.fit"},
            },
        }

    @staticmethod
    def _text_update(text: str) -> dict:
        return {
            "update_id": 4,
            "message": {
                "message_id": 4,
                "chat": {"id": 535004713},
                "text": text,
            },
        }

    def _queue_pending_fit(self, temp_dir: str, client: FakeTelegramClient, paths) -> None:
        handle_update(update=self._fit_update(), config=self._config(temp_dir), client=client, paths=paths)
        client.messages.clear()

    @staticmethod
    def _result(*, status: str, output_path: str | None = None, caption: str | None = None, error: str | None = None):
        from runstats.automation import AutomationResult

        return AutomationResult(
            status=status,
            input_path="input.fit",
            sha256="sha",
            template="glass_slab",
            output_path=output_path,
            distance_km=5.0,
            moving_time_s=1500.0,
            avg_pace_min_per_km=5.0,
            location=None,
            caption=caption,
            error=error,
        )


if __name__ == "__main__":
    unittest.main()
