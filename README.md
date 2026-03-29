# RunStats

Render transparent run-stat overlays from local `.fit` and `.gpx` activity files.

## Install

```bash
python -m pip install -e .
```

## Usage

Default interactive flow:

```bash
python plot_gpx.py
```

Console entrypoint:

```bash
runstats --auto
```

Machine-facing automation entrypoint:

```bash
runstats-automation --input C:\RunStatsAutomation\processing\22321337482_ACTIVITY.fit
```

Direct Telegram bot runner:

```bash
runstats-telegram-bot --chat-id 535004713 --workspace C:\RunStatsAutomation
```

Render the Instagram Story overlay directly:

```bash
python plot_gpx.py --input 21760678383_ACTIVITY.fit --template story_overlay --output story_overlay.png
```

Render the alternate card layout:

```bash
python plot_gpx.py --input activity.gpx --template clean_card --output clean_card.png
```

Render the Stitch-inspired Instagram Story layout:

```bash
python plot_gpx.py --input 21654870128_ACTIVITY.fit --template neon_data_story --output neon_data_story.png
```

If timing data is missing and you still want the route art:

```bash
python plot_gpx.py --input activity.gpx --route-only --output route_only.png
```

## Templates

- `story_overlay`: transparent 1080x1920 Instagram Story-style overlay
- `clean_card`: alternate square card layout
- `neon_data_story`: Stitch-inspired 1080x1920 Instagram Story overlay

## Useful flags

- `--mode solid|gradient|auto`
- `--title "MORNING RUN"`
- `--no-title`
- `--auto`
- `--search-dir .`

## Telegram Automation

For the direct bot workflow without n8n, use:

- [`docs/telegram_bot_runner.md`](/C:/Users/Eurus/Documents/GitHub/RunStats/docs/telegram_bot_runner.md)

For the earlier n8n-based approach, keep using:

- [`docs/telegram_ingest_automation.md`](/C:/Users/Eurus/Documents/GitHub/RunStats/docs/telegram_ingest_automation.md)
- [`n8n/telegram_ingest_workflow.example.json`](/C:/Users/Eurus/Documents/GitHub/RunStats/n8n/telegram_ingest_workflow.example.json)
