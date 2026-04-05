from __future__ import annotations

import argparse
import json
import mimetypes
import os
import shutil
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .automation import (
    DEFAULT_AUTOMATION_TEMPLATE,
    DEFAULT_WORKSPACE_ROOT,
    AutomationPaths,
    ensure_workspace,
    resolve_automation_paths,
    run_automation,
    utc_now_iso,
)
from .templates import TEMPLATE_NAMES


DEFAULT_POLL_TIMEOUT_S = 30
DEFAULT_REQUEST_TIMEOUT_S = 60
DEFAULT_RETRY_DELAY_S = 3
OFFSET_FILENAME = "telegram_update_offset.txt"
TELEGRAM_LOG_FILENAME = "telegram_bot_events.jsonl"
PENDING_REQUESTS_FILENAME = "telegram_pending_requests.json"


@dataclass(frozen=True)
class TelegramBotConfig:
    token: str
    workspace_root: Path
    template: str
    auto_process_uploads: bool
    route_mode: str
    allowed_chat_id: int | None
    title: str | None
    location: str | None
    no_geocode: bool
    poll_timeout_s: int
    request_timeout_s: int
    retry_delay_s: int
    once: bool
    offset_path: Path | None


@dataclass(frozen=True)
class IncomingDocument:
    update_id: int
    chat_id: int
    message_id: int | None
    file_id: str
    file_name: str
    mime_type: str | None


class TelegramApiError(RuntimeError):
    pass


class TelegramBotClient:
    def __init__(self, token: str, request_timeout_s: int = DEFAULT_REQUEST_TIMEOUT_S) -> None:
        self.token = token
        self.request_timeout_s = request_timeout_s
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.file_base_url = f"https://api.telegram.org/file/bot{token}"

    def get_updates(self, *, offset: int | None, timeout_s: int) -> list[dict[str, Any]]:
        payload: dict[str, Any] = {"timeout": timeout_s}
        if offset is not None:
            payload["offset"] = offset
        response = self._post_json("getUpdates", payload)
        result = response.get("result")
        if not isinstance(result, list):
            raise TelegramApiError("Telegram getUpdates returned an unexpected payload.")
        return [item for item in result if isinstance(item, dict)]

    def get_file_path(self, file_id: str) -> str:
        response = self._post_json("getFile", {"file_id": file_id})
        result = response.get("result")
        if not isinstance(result, dict):
            raise TelegramApiError("Telegram getFile returned an unexpected payload.")
        file_path = result.get("file_path")
        if not isinstance(file_path, str) or not file_path:
            raise TelegramApiError("Telegram getFile did not return a file path.")
        return file_path

    def download_file(self, file_path: str) -> bytes:
        request = Request(f"{self.file_base_url}/{file_path}")
        with urlopen(request, timeout=self.request_timeout_s) as response:
            return response.read()

    def send_message(
        self,
        chat_id: int,
        text: str,
        *,
        reply_markup: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {"chat_id": chat_id, "text": text}
        if reply_markup is not None:
            payload["reply_markup"] = reply_markup
        return self._post_json("sendMessage", payload)

    def send_document(
        self,
        chat_id: int,
        document_path: str | Path,
        caption: str | None = None,
        *,
        reply_markup: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        path = Path(document_path)
        content_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
        fields = {
            "chat_id": str(chat_id),
        }
        if caption:
            fields["caption"] = caption
        if reply_markup is not None:
            fields["reply_markup"] = json.dumps(reply_markup, ensure_ascii=True)
        files = {
            "document": (path.name, path.read_bytes(), content_type),
        }
        return self._post_multipart("sendDocument", fields=fields, files=files)

    def _post_json(self, method: str, payload: dict[str, Any]) -> dict[str, Any]:
        request = Request(
            f"{self.base_url}/{method}",
            data=json.dumps(payload).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.request_timeout_s) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (OSError, HTTPError, URLError) as exc:
            raise TelegramApiError(str(exc)) from exc
        if raw.get("ok") is not True:
            raise TelegramApiError(str(raw.get("description") or f"Telegram API call failed: {method}"))
        return raw

    def _post_multipart(
        self,
        method: str,
        *,
        fields: dict[str, str],
        files: dict[str, tuple[str, bytes, str]],
    ) -> dict[str, Any]:
        boundary = f"----runstats-{uuid.uuid4().hex}"
        body = build_multipart_body(fields=fields, files=files, boundary=boundary)
        request = Request(
            f"{self.base_url}/{method}",
            data=body,
            headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
            method="POST",
        )
        try:
            with urlopen(request, timeout=self.request_timeout_s) as response:
                raw = json.loads(response.read().decode("utf-8"))
        except (OSError, HTTPError, URLError) as exc:
            raise TelegramApiError(str(exc)) from exc
        if raw.get("ok") is not True:
            raise TelegramApiError(str(raw.get("description") or f"Telegram API call failed: {method}"))
        return raw


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Poll Telegram for .fit uploads and reply with RunStats renders.")
    parser.add_argument("--token", default=os.environ.get("TELEGRAM_BOT_TOKEN"), help="Telegram bot token.")
    parser.add_argument(
        "--chat-id",
        type=int,
        default=_read_optional_int_env("RUNSTATS_TELEGRAM_CHAT_ID"),
        help="Optional allowed Telegram chat ID. Other chats are ignored.",
    )
    parser.add_argument(
        "--workspace",
        default=str(DEFAULT_WORKSPACE_ROOT),
        help="Workspace root used for processing, exports, logs, and offsets.",
    )
    parser.add_argument(
        "--template",
        default=DEFAULT_AUTOMATION_TEMPLATE,
        help="Template to render for valid FIT uploads.",
    )
    parser.add_argument(
        "--auto-process-uploads",
        action="store_true",
        help="Render the configured template immediately when a .FIT upload arrives.",
    )
    parser.add_argument(
        "--mode",
        default="auto",
        choices=("auto", "solid", "gradient"),
        help="Route rendering mode. 'auto' uses the automation default.",
    )
    parser.add_argument("--title", default=None, help="Optional title override passed to the renderer.")
    parser.add_argument("--no-title", action="store_true", help="Hide title text on generated renders.")
    parser.add_argument("--location", default=None, help="Optional location override.")
    parser.add_argument("--no-geocode", action="store_true", help="Disable reverse geocoding.")
    parser.add_argument("--once", action="store_true", help="Process currently available updates once, then exit.")
    parser.add_argument(
        "--poll-timeout",
        type=int,
        default=DEFAULT_POLL_TIMEOUT_S,
        help="Telegram long-poll timeout in seconds.",
    )
    parser.add_argument(
        "--request-timeout",
        type=int,
        default=DEFAULT_REQUEST_TIMEOUT_S,
        help="HTTP timeout in seconds for Telegram API requests.",
    )
    parser.add_argument(
        "--retry-delay",
        type=int,
        default=DEFAULT_RETRY_DELAY_S,
        help="Delay before retrying after polling or send errors.",
    )
    parser.add_argument(
        "--offset-path",
        default=None,
        help="Optional path for the persisted Telegram update offset.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    if not args.token:
        parser.error("Telegram bot token is required. Pass --token or set TELEGRAM_BOT_TOKEN.")

    workspace_root = Path(args.workspace).expanduser().resolve()
    paths = resolve_automation_paths(workspace_root=workspace_root)
    ensure_workspace(paths)
    offset_path = (
        Path(args.offset_path).expanduser().resolve()
        if args.offset_path
        else paths.logs_dir / OFFSET_FILENAME
    )

    config = TelegramBotConfig(
        token=args.token,
        workspace_root=workspace_root,
        template=args.template,
        auto_process_uploads=args.auto_process_uploads,
        route_mode=args.mode,
        allowed_chat_id=args.chat_id,
        title=None if args.no_title else args.title,
        location=args.location,
        no_geocode=args.no_geocode,
        poll_timeout_s=args.poll_timeout,
        request_timeout_s=args.request_timeout,
        retry_delay_s=args.retry_delay,
        once=args.once,
        offset_path=offset_path,
    )
    client = TelegramBotClient(config.token, request_timeout_s=config.request_timeout_s)
    run_bot(config, client, paths)
    return 0


def run_bot(config: TelegramBotConfig, client: TelegramBotClient, paths: AutomationPaths | None = None) -> None:
    resolved_paths = paths or resolve_automation_paths(workspace_root=config.workspace_root)
    ensure_workspace(resolved_paths)
    offset = load_offset(config.offset_path)

    while True:
        try:
            updates = client.get_updates(offset=offset, timeout_s=config.poll_timeout_s)
        except TelegramApiError as exc:
            append_bot_event(resolved_paths.logs_dir / TELEGRAM_LOG_FILENAME, "poll_error", {"error": str(exc)})
            if config.once:
                break
            time.sleep(config.retry_delay_s)
            continue

        if not updates:
            if config.once:
                break
            continue

        for update in updates:
            update_id = get_update_id(update)
            if update_id is None:
                continue

            try:
                handle_update(update=update, config=config, client=client, paths=resolved_paths)
            except Exception as exc:
                append_bot_event(
                    resolved_paths.logs_dir / TELEGRAM_LOG_FILENAME,
                    "update_error",
                    {"error": str(exc), "update_id": update_id},
                )
            offset = update_id + 1
            save_offset(config.offset_path, offset)

        if config.once:
            break


def handle_update(*, update: dict[str, Any], config: TelegramBotConfig, client: TelegramBotClient, paths: AutomationPaths) -> None:
    pending_path = paths.logs_dir / PENDING_REQUESTS_FILENAME
    pending_requests = load_pending_requests(pending_path)
    message = update.get("message")
    chat_id = extract_chat_id(update)
    if chat_id is None:
        return
    if config.allowed_chat_id is not None and chat_id != config.allowed_chat_id:
        append_bot_event(
            paths.logs_dir / TELEGRAM_LOG_FILENAME,
            "ignored_chat",
            {"chat_id": chat_id, "update_id": get_update_id(update)},
        )
        return

    text = message.get("text") if isinstance(message, dict) else None
    if isinstance(text, str):
        if handle_text_message(
            chat_id=chat_id,
            text=text,
            pending_requests=pending_requests,
            pending_path=pending_path,
            config=config,
            client=client,
            paths=paths,
        ):
            return

    incoming = extract_document(update)
    if incoming is None:
        return
    if not incoming.file_name.lower().endswith(".fit"):
        client.send_message(incoming.chat_id, "Send a .FIT document to this bot to start processing.")
        append_bot_event(
            paths.logs_dir / TELEGRAM_LOG_FILENAME,
            "rejected_non_fit",
            {"chat_id": incoming.chat_id, "file_name": incoming.file_name, "update_id": incoming.update_id},
        )
        return

    processing_path = write_processing_file(incoming, client, paths.processing_dir)
    if config.auto_process_uploads:
        client.send_message(
            incoming.chat_id,
            f"Received {processing_path.name}. Rendering {config.template} now.",
            reply_markup=remove_keyboard_markup(),
        )
        _process_input_path(
            chat_id=incoming.chat_id,
            input_path=processing_path,
            selected_templates=[config.template],
            config=config,
            client=client,
            paths=paths,
        )
        append_bot_event(
            paths.logs_dir / TELEGRAM_LOG_FILENAME,
            "queued_fit_auto_processed",
            {"chat_id": incoming.chat_id, "file_name": processing_path.name, "update_id": incoming.update_id, "template": config.template},
        )
        return

    pending_requests[str(incoming.chat_id)] = {
        "input_path": str(processing_path),
        "file_name": processing_path.name,
        "update_id": incoming.update_id,
        "created_at": utc_now_iso(),
        "selected_templates": [],
        "selection_stage": "awaiting_templates",
    }
    save_pending_requests(pending_path, pending_requests)
    client.send_message(
        incoming.chat_id,
        build_template_prompt(selected_templates=[]),
        reply_markup=build_template_keyboard(),
    )
    append_bot_event(
        paths.logs_dir / TELEGRAM_LOG_FILENAME,
        "queued_fit",
        {"chat_id": incoming.chat_id, "file_name": processing_path.name, "update_id": incoming.update_id},
    )


def handle_text_message(
    *,
    chat_id: int,
    text: str,
    pending_requests: dict[str, dict[str, Any]],
    pending_path: Path,
    config: TelegramBotConfig,
    client: TelegramBotClient,
    paths: AutomationPaths,
) -> bool:
    normalized = text.strip()
    pending = _get_pending_request(pending_requests, chat_id)
    if normalized.lower() == "/start":
        client.send_message(
            chat_id,
            "Send a .FIT document, then choose one or more templates. Send /done when finished.",
            reply_markup=build_template_keyboard(),
        )
        return True
    if normalized.lower() == "/templates":
        selected_templates = _get_selected_templates(pending) if pending is not None else None
        client.send_message(
            chat_id,
            build_template_prompt(selected_templates=selected_templates),
            reply_markup=build_template_keyboard(),
        )
        return True
    if normalized.lower() == "/done":
        if pending is None:
            client.send_message(chat_id, "Send a .FIT document first, then choose templates.", reply_markup=remove_keyboard_markup())
            return True
        return _finalize_pending_request(
            chat_id=chat_id,
            pending=pending,
            pending_requests=pending_requests,
            pending_path=pending_path,
            config=config,
            client=client,
            paths=paths,
        )
    if normalized.lower() == "/cancel":
        if pending is None:
            client.send_message(chat_id, "There is no pending FIT upload to cancel.", reply_markup=remove_keyboard_markup())
            return True
        return _cancel_pending_request(
            chat_id=chat_id,
            pending=pending,
            pending_requests=pending_requests,
            pending_path=pending_path,
            client=client,
            paths=paths,
        )
    if pending is None:
        return False

    template = resolve_template_choice(normalized)
    if template is None:
        client.send_message(
            chat_id,
            "Pick one or more template names below, then send /done when finished.",
            reply_markup=build_template_keyboard(),
        )
        return True

    input_path = Path(str(pending.get("input_path", "")))
    if not input_path.exists():
        pending_requests.pop(str(chat_id), None)
        save_pending_requests(pending_path, pending_requests)
        client.send_message(chat_id, "I could not find the pending FIT file. Send it again.", reply_markup=remove_keyboard_markup())
        return True

    selected_templates = _get_selected_templates(pending)
    if template in selected_templates:
        client.send_message(
            chat_id,
            f"{template} is already selected. Pick another template or send /done.",
            reply_markup=build_template_keyboard(),
        )
        return True

    selected_templates.append(template)
    pending["selected_templates"] = selected_templates
    pending["selection_stage"] = "awaiting_templates"
    pending_requests[str(chat_id)] = pending
    save_pending_requests(pending_path, pending_requests)
    client.send_message(
        chat_id,
        build_selection_status_message(selected_templates),
        reply_markup=build_template_keyboard(),
    )
    append_bot_event(
        paths.logs_dir / TELEGRAM_LOG_FILENAME,
        "selected_template",
        {"chat_id": chat_id, "template": template, "selected_templates": selected_templates},
    )
    return True


def _get_pending_request(pending_requests: dict[str, dict[str, Any]], chat_id: int) -> dict[str, Any] | None:
    pending = pending_requests.get(str(chat_id))
    if not isinstance(pending, dict):
        return None
    normalized = dict(pending)
    normalized["selected_templates"] = _get_selected_templates(normalized)
    normalized["selection_stage"] = str(normalized.get("selection_stage") or "awaiting_templates")
    return normalized


def _get_selected_templates(pending: dict[str, Any] | None) -> list[str]:
    if not isinstance(pending, dict):
        return []
    raw = pending.get("selected_templates")
    if not isinstance(raw, list):
        return []
    return [str(value) for value in raw if isinstance(value, str)]


def _finalize_pending_request(
    *,
    chat_id: int,
    pending: dict[str, Any],
    pending_requests: dict[str, dict[str, Any]],
    pending_path: Path,
    config: TelegramBotConfig,
    client: TelegramBotClient,
    paths: AutomationPaths,
) -> bool:
    selected_templates = _get_selected_templates(pending)
    if not selected_templates:
        client.send_message(
            chat_id,
            "Choose at least one template before sending /done.",
            reply_markup=build_template_keyboard(),
        )
        return True

    input_path = Path(str(pending.get("input_path", "")))
    if not input_path.exists():
        pending_requests.pop(str(chat_id), None)
        save_pending_requests(pending_path, pending_requests)
        client.send_message(chat_id, "I could not find the pending FIT file. Send it again.", reply_markup=remove_keyboard_markup())
        return True

    _process_input_path(
        chat_id=chat_id,
        input_path=input_path,
        selected_templates=selected_templates,
        config=config,
        client=client,
        paths=paths,
    )

    pending_requests.pop(str(chat_id), None)
    save_pending_requests(pending_path, pending_requests)
    return True


def _process_input_path(
    *,
    chat_id: int,
    input_path: Path,
    selected_templates: list[str],
    config: TelegramBotConfig,
    client: TelegramBotClient,
    paths: AutomationPaths,
) -> None:
    input_path = Path(input_path)

    saw_success = False
    resent_duplicate = False
    saw_error = False

    for template in selected_templates:
        result = run_automation(
            input_path=input_path,
            template=template,
            route_mode=config.route_mode,
            workspace_root=paths.root,
            title=config.title,
            location=config.location,
            no_geocode=config.no_geocode,
        )

        if result.status == "success":
            try:
                client.send_document(chat_id, result.output_path, result.caption, reply_markup=remove_keyboard_markup())
            except TelegramApiError as exc:
                move_to_archive(input_path, paths.failed_delivery_dir)
                append_bot_event(
                    paths.logs_dir / TELEGRAM_LOG_FILENAME,
                    "delivery_failed",
                    {"chat_id": chat_id, "input_path": str(input_path), "output_path": result.output_path, "error": str(exc)},
                )
                raise
            saw_success = True
            append_bot_event(
                paths.logs_dir / TELEGRAM_LOG_FILENAME,
                "sent_render",
                {"chat_id": chat_id, "input_path": str(input_path), "output_path": result.output_path, "template": template},
            )
            continue

        if result.status == "duplicate":
            duplicate_output = Path(result.output_path) if result.output_path else None
            if duplicate_output is not None and duplicate_output.exists():
                try:
                    client.send_document(chat_id, duplicate_output, result.caption, reply_markup=remove_keyboard_markup())
                except TelegramApiError as exc:
                    move_to_archive(input_path, paths.failed_delivery_dir)
                    append_bot_event(
                        paths.logs_dir / TELEGRAM_LOG_FILENAME,
                        "delivery_failed",
                        {"chat_id": chat_id, "input_path": str(input_path), "output_path": str(duplicate_output), "error": str(exc)},
                    )
                    raise
                resent_duplicate = True
                append_bot_event(
                    paths.logs_dir / TELEGRAM_LOG_FILENAME,
                    "resent_duplicate_render",
                    {"chat_id": chat_id, "input_path": str(input_path), "output_path": str(duplicate_output), "template": template},
                )
            else:
                saw_error = True
                client.send_message(
                    chat_id,
                    f"{template} was already processed, but I could not find the saved PNG. Skipping it.",
                    reply_markup=remove_keyboard_markup(),
                )
                append_bot_event(
                    paths.logs_dir / TELEGRAM_LOG_FILENAME,
                    "missing_duplicate_output",
                    {"chat_id": chat_id, "input_path": str(input_path), "template": template, "output_path": result.output_path},
                )
            continue

        saw_error = True
        client.send_message(
            chat_id,
            f"RunStats could not render {template}. {result.error or ''}".strip(),
            reply_markup=remove_keyboard_markup(),
        )
        append_bot_event(
            paths.logs_dir / TELEGRAM_LOG_FILENAME,
            "render_failed",
            {"chat_id": chat_id, "input_path": str(input_path), "error": result.error, "template": template},
        )

    if saw_success or (resent_duplicate and saw_error):
        move_to_archive(input_path, paths.processed_dir)
    elif resent_duplicate:
        move_to_archive(input_path, paths.processed_duplicates_dir)
        append_bot_event(
            paths.logs_dir / TELEGRAM_LOG_FILENAME,
            "duplicate_fit",
            {"chat_id": chat_id, "input_path": str(input_path), "templates": selected_templates},
        )
    else:
        move_to_archive(input_path, paths.failed_render_dir)
    return True


def _cancel_pending_request(
    *,
    chat_id: int,
    pending: dict[str, Any],
    pending_requests: dict[str, dict[str, Any]],
    pending_path: Path,
    client: TelegramBotClient,
    paths: AutomationPaths,
) -> bool:
    input_path = Path(str(pending.get("input_path", "")))
    if input_path.exists():
        input_path.unlink()
    pending_requests.pop(str(chat_id), None)
    save_pending_requests(pending_path, pending_requests)
    client.send_message(chat_id, "Cancelled this FIT upload. Send a new .FIT document when you're ready.", reply_markup=remove_keyboard_markup())
    append_bot_event(
        paths.logs_dir / TELEGRAM_LOG_FILENAME,
        "cancelled_fit",
        {"chat_id": chat_id, "input_path": str(input_path)},
    )
    return True


def extract_document(update: dict[str, Any]) -> IncomingDocument | None:
    message = update.get("message")
    if not isinstance(message, dict):
        return None
    document = message.get("document")
    if not isinstance(document, dict):
        return None
    chat = message.get("chat")
    if not isinstance(chat, dict):
        return None
    file_id = document.get("file_id")
    file_name = document.get("file_name")
    chat_id = chat.get("id")
    if not isinstance(file_id, str) or not isinstance(file_name, str) or not isinstance(chat_id, int):
        return None
    update_id = get_update_id(update)
    if update_id is None:
        return None
    message_id = message.get("message_id")
    return IncomingDocument(
        update_id=update_id,
        chat_id=chat_id,
        message_id=message_id if isinstance(message_id, int) else None,
        file_id=file_id,
        file_name=file_name,
        mime_type=document.get("mime_type") if isinstance(document.get("mime_type"), str) else None,
    )


def write_processing_file(incoming: IncomingDocument, client: TelegramBotClient, processing_dir: str | Path) -> Path:
    file_path = client.get_file_path(incoming.file_id)
    contents = client.download_file(file_path)
    target = unique_processing_path(processing_dir, incoming.file_name, incoming.update_id)
    target.write_bytes(contents)
    return target


def unique_processing_path(processing_dir: str | Path, original_name: str, update_id: int) -> Path:
    directory = Path(processing_dir)
    directory.mkdir(parents=True, exist_ok=True)
    safe_name = sanitize_filename(original_name)
    suffix = Path(safe_name).suffix or ".fit"
    stem = Path(safe_name).stem or "activity"
    candidate = directory / f"{stem}_{update_id}{suffix}"
    counter = 1
    while candidate.exists():
        candidate = directory / f"{stem}_{update_id}_{counter}{suffix}"
        counter += 1
    return candidate


def sanitize_filename(value: str) -> str:
    sanitized = "".join("_" if char in '<>:"/\\|?*\x00' or ord(char) < 32 else char for char in value).strip()
    return sanitized or "upload.fit"


def move_to_archive(source: str | Path, destination_dir: str | Path) -> Path:
    source_path = Path(source)
    destination = unique_archive_path(destination_dir, source_path.name)
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.move(str(source_path), str(destination))
    return destination


def unique_archive_path(destination_dir: str | Path, original_name: str) -> Path:
    directory = Path(destination_dir)
    stem = Path(original_name).stem or "activity"
    suffix = Path(original_name).suffix
    candidate = directory / original_name
    counter = 1
    while candidate.exists():
        candidate = directory / f"{stem}_{counter}{suffix}"
        counter += 1
    return candidate


def build_multipart_body(
    *,
    fields: dict[str, str],
    files: dict[str, tuple[str, bytes, str]],
    boundary: str,
) -> bytes:
    chunks: list[bytes] = []
    for name, value in fields.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"),
                value.encode("utf-8"),
                b"\r\n",
            ]
        )
    for name, (filename, content, content_type) in files.items():
        chunks.extend(
            [
                f"--{boundary}\r\n".encode("utf-8"),
                (
                    f'Content-Disposition: form-data; name="{name}"; filename="{filename}"\r\n'
                    f"Content-Type: {content_type}\r\n\r\n"
                ).encode("utf-8"),
                content,
                b"\r\n",
            ]
        )
    chunks.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(chunks)


def load_offset(path: str | Path | None) -> int | None:
    if path is None:
        return None
    offset_path = Path(path)
    if not offset_path.exists():
        return None
    try:
        raw = offset_path.read_text(encoding="utf-8").strip()
    except OSError:
        return None
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def save_offset(path: str | Path | None, value: int) -> None:
    if path is None:
        return
    offset_path = Path(path)
    offset_path.parent.mkdir(parents=True, exist_ok=True)
    offset_path.write_text(str(value), encoding="utf-8")


def append_bot_event(path: str | Path, event: str, payload: dict[str, Any]) -> None:
    event_path = Path(path)
    event_path.parent.mkdir(parents=True, exist_ok=True)
    record = {
        "timestamp": utc_now_iso(),
        "event": event,
        **payload,
    }
    with event_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(record, ensure_ascii=True))
        handle.write("\n")


def get_update_id(update: dict[str, Any]) -> int | None:
    value = update.get("update_id")
    return value if isinstance(value, int) else None


def extract_chat_id(update: dict[str, Any]) -> int | None:
    message = update.get("message")
    if not isinstance(message, dict):
        return None
    chat = message.get("chat")
    if not isinstance(chat, dict):
        return None
    value = chat.get("id")
    return value if isinstance(value, int) else None


def load_pending_requests(path: str | Path) -> dict[str, dict[str, Any]]:
    pending_path = Path(path)
    if not pending_path.exists():
        return {}
    try:
        raw = json.loads(pending_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}
    if not isinstance(raw, dict):
        return {}
    result: dict[str, dict[str, Any]] = {}
    for key, value in raw.items():
        if isinstance(key, str) and isinstance(value, dict):
            normalized: dict[str, Any] = {}
            for inner_key, inner_value in value.items():
                normalized_key = str(inner_key)
                if normalized_key == "selected_templates" and isinstance(inner_value, list):
                    normalized[normalized_key] = [str(item) for item in inner_value if isinstance(item, str)]
                else:
                    normalized[normalized_key] = str(inner_value)
            normalized.setdefault("selected_templates", [])
            normalized.setdefault("selection_stage", "awaiting_templates")
            result[key] = normalized
    return result


def save_pending_requests(path: str | Path, pending_requests: dict[str, dict[str, Any]]) -> None:
    pending_path = Path(path)
    pending_path.parent.mkdir(parents=True, exist_ok=True)
    pending_path.write_text(json.dumps(pending_requests, indent=2, sort_keys=True), encoding="utf-8")


def build_template_prompt(*, selected_templates: list[str] | None = None) -> str:
    lines = [
        "Choose one or more templates by name or number.",
        "Send /done when finished or /cancel to discard this FIT.",
    ]
    if selected_templates is not None:
        selected = ", ".join(selected_templates) if selected_templates else "none yet"
        lines.append(f"Selected: {selected}")
    for index, name in enumerate(TEMPLATE_NAMES, start=1):
        lines.append(f"{index}. {name}")
    return "\n".join(lines)


def build_selection_status_message(selected_templates: list[str]) -> str:
    selected = ", ".join(selected_templates) if selected_templates else "none yet"
    return f"Selected templates: {selected}\nPick another template or send /done."


def build_template_keyboard() -> dict[str, Any]:
    rows: list[list[dict[str, str]]] = []
    current_row: list[dict[str, str]] = []
    for name in TEMPLATE_NAMES:
        current_row.append({"text": name})
        if len(current_row) == 2:
            rows.append(current_row)
            current_row = []
    if current_row:
        rows.append(current_row)
    rows.append([{"text": "/done"}, {"text": "/cancel"}])
    return {"keyboard": rows, "resize_keyboard": True, "one_time_keyboard": False}


def remove_keyboard_markup() -> dict[str, bool]:
    return {"remove_keyboard": True}


def resolve_template_choice(value: str) -> str | None:
    normalized = value.strip().lower()
    if not normalized:
        return None
    if normalized.isdigit():
        index = int(normalized)
        if 1 <= index <= len(TEMPLATE_NAMES):
            return TEMPLATE_NAMES[index - 1]
        return None
    for name in TEMPLATE_NAMES:
        if normalized == name.lower():
            return name
    return None


def _read_optional_int_env(name: str) -> int | None:
    raw = os.environ.get(name)
    if raw is None or raw.strip() == "":
        return None
    try:
        return int(raw.strip())
    except ValueError:
        return None


__all__ = [
    "DEFAULT_POLL_TIMEOUT_S",
    "IncomingDocument",
    "TelegramApiError",
    "TelegramBotClient",
    "TelegramBotConfig",
    "append_bot_event",
    "build_multipart_body",
    "build_parser",
    "build_template_keyboard",
    "build_template_prompt",
    "build_selection_status_message",
    "extract_document",
    "handle_text_message",
    "handle_update",
    "load_offset",
    "load_pending_requests",
    "main",
    "move_to_archive",
    "remove_keyboard_markup",
    "resolve_template_choice",
    "run_bot",
    "sanitize_filename",
    "save_offset",
    "save_pending_requests",
    "unique_processing_path",
    "write_processing_file",
]


if __name__ == "__main__":
    raise SystemExit(main())
