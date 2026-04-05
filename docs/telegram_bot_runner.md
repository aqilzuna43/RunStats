# Direct Telegram Bot Runner

This repo includes a lightweight Telegram polling bot that does not require n8n.

It uses the Telegram Bot API directly, downloads `.fit` uploads into the automation workspace, runs the existing machine-facing renderer, sends the generated PNG back to Telegram, and archives the source file.

## Command

```powershell
runstats-telegram-bot --chat-id 535004713 --workspace "C:\RunStatsAutomation"
```

Environment variables:

- `TELEGRAM_BOT_TOKEN`
- `RUNSTATS_TELEGRAM_CHAT_ID` (optional if you pass `--chat-id`)

Recommended first run:

```powershell
$env:TELEGRAM_BOT_TOKEN="REPLACE_ME"
$env:RUNSTATS_TELEGRAM_CHAT_ID="535004713"
python -m runstats.telegram_bot --once --workspace "C:\RunStatsAutomation"
```

Long-running bot:

```powershell
python -m runstats.telegram_bot --workspace "C:\RunStatsAutomation"
```

Long-running bot with immediate rendering on `.fit` upload:

```powershell
python -m runstats.telegram_bot --workspace "C:\RunStatsAutomation" --template glass_slab --auto-process-uploads
```

## Behavior

- Accepts `.fit` documents only
- By default, after a FIT upload, asks you which template to use
- Accepts template replies by name or by number
- Ignores other chats when `--chat-id` is set
- Downloads uploads to `processing`
- Calls `runstats.automation.run_automation()`
- Sends the rendered PNG back on success
- With `--auto-process-uploads`, renders the configured `--template` immediately without waiting for `/done`
- Moves FIT files to:
  - `processed`
  - `processed\duplicates`
  - `failed\render`
  - `failed\delivery`

Bot-specific logs:

- `logs\telegram_bot_events.jsonl`
- `logs\telegram_update_offset.txt`

## Notes

- The bot uses long polling, so it can run from a normal terminal or Task Scheduler.
- Only one Telegram consumer should be attached to the same bot token at a time. Do not run the direct bot and an n8n Telegram Trigger against the same bot simultaneously.
- The bot depends only on the Python standard library plus the repo's existing RunStats dependencies.
- If you rotate the Telegram token, restart the bot process with the new token.
- The same FIT can now be rendered in multiple templates. Dedupe is template-aware.
