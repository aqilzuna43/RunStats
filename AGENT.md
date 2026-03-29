# RunStats Agent Reference

## Purpose

`RunStats` renders PNG run-stat overlays from local `.fit` and `.gpx` activity files.

Primary entrypoint:

```bash
python plot_gpx.py
```

Installed console entrypoint:

```bash
runstats --auto
```

Automation console entrypoint:

```bash
runstats-automation --input C:\RunStatsAutomation\processing\22321337482_ACTIVITY.fit
```

Direct Telegram bot entrypoint:

```bash
runstats-telegram-bot --chat-id 535004713 --workspace C:\RunStatsAutomation
```

## Current Template Inventory

The code currently exposes 8 template names in [`runstats/templates.py`](./runstats/templates.py):

- `story_overlay`
- `clean_card`
- `glass_slab`
- `clipboard_card`
- `neon_split`
- `ghost_overlay`
- `kinetic_glass`
- `neon_data_story`

In practice, the newer stylized exports are:

- `clean_card`
- `glass_slab`
- `clipboard_card`
- `neon_split`
- `ghost_overlay`
- `kinetic_glass`
- `neon_data_story`

Most recent verified FIT input:

- `22321337482_ACTIVITY.fit`

Most recent exported outputs:

- `clean_card.png`
- `glass_slab.png`
- `clipboard_card.png`
- `neon_split.png`

## Repo Shape

Key files:

- [`plot_gpx.py`](./plot_gpx.py): thin script wrapper
- [`runstats/cli.py`](./runstats/cli.py): CLI flow and template selection
- [`runstats/automation.py`](./runstats/automation.py): JSON-emitting automation entrypoint for n8n/Telegram
- [`runstats/telegram_bot.py`](./runstats/telegram_bot.py): lightweight Telegram polling bot runner
- [`runstats/ingest.py`](./runstats/ingest.py): FIT/GPX parsing
- [`runstats/models.py`](./runstats/models.py): immutable activity models and cached derived data
- [`runstats/render.py`](./runstats/render.py): route plotting
- [`runstats/templates.py`](./runstats/templates.py): template renderers
- [`runstats/template_support.py`](./runstats/template_support.py): shared figure/text/font helpers
- [`tests/test_metrics.py`](./tests/test_metrics.py): metrics and model tests
- [`tests/test_automation.py`](./tests/test_automation.py): automation command and dedupe tests
- [`tests/test_telegram_bot.py`](./tests/test_telegram_bot.py): Telegram bot workflow tests
- [`tests/test_package.py`](./tests/test_package.py): import-light package regression test

Design reference:

- [`running-stats-overlay.md`](./running-stats-overlay.md)

## Environment and Dependencies

Project metadata lives in [`pyproject.toml`](./pyproject.toml).

Install locally:

```bash
python -m pip install -e .
```

Declared runtime deps:

- `fitparse`
- `gpxpy`
- `matplotlib`
- `numpy`

## Verified Commands

Tests:

```bash
python -m unittest -v
python -m unittest discover -s tests -v
```

Export examples:

```bash
python plot_gpx.py --input 22321337482_ACTIVITY.fit --template clean_card --output clean_card.png
python plot_gpx.py --input 22321337482_ACTIVITY.fit --template glass_slab --output glass_slab.png
python plot_gpx.py --input 22321337482_ACTIVITY.fit --template clipboard_card --output clipboard_card.png
python plot_gpx.py --input 22321337482_ACTIVITY.fit --template neon_split --output neon_split.png
```

## Important Current State

- The package import is intentionally light: [`runstats/__init__.py`](./runstats/__init__.py) lazily imports the CLI so tests can import `runstats` without pulling rendering deps immediately.
- [`runstats/models.py`](./runstats/models.py) now caches derived route arrays and timestamp/speed summaries; prefer those properties instead of rebuilding lists from `points`.
- Shared font and figure helpers were split into [`runstats/template_support.py`](./runstats/template_support.py) to keep template changes localized.
- The worktree is dirty. Do not assume a clean Git baseline.
- There are tracked `__pycache__` artifacts still showing up in Git state from earlier work. `.gitignore` now ignores them, but the index may still contain staged deletions/additions that should be handled deliberately.
- There are also user-owned generated PNG and FIT file changes in the repo root. Do not delete or revert them unless explicitly asked.

## Practical Guidance For The Next Agent

- If the task is about layout/design, start in [`runstats/templates.py`](./runstats/templates.py) and keep helper-only changes in [`runstats/template_support.py`](./runstats/template_support.py).
- If the task is about performance or data quality, inspect [`runstats/ingest.py`](./runstats/ingest.py), [`runstats/models.py`](./runstats/models.py), and [`runstats/render.py`](./runstats/render.py) together.
- If you need another export set, use `22321337482_ACTIVITY.fit` unless the user specifies a different activity file.
- If you need to validate quickly, run `python -m unittest -v` before touching render outputs.
