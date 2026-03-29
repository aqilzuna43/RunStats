# RunStats Architecture

This repo is a local, file-driven PNG overlay generator for running activities.

## Container Diagram

```mermaid
flowchart LR
    U[User / Windows Shell] --> B[Batch Helpers<br/>export_glass.bat / export_all.bat]
    U --> C[CLI Entry<br/>plot_gpx.py / runstats.cli]
    TGB[TG Bot] --> N8[n8n Workflow]
    TGU[Telegram User] --> TB[Telegram Bot Runner<br/>runstats.telegram_bot]
    B --> C
    N8 --> A[Automation Entry<br/>runstats.automation]

    C --> I[Ingest Layer<br/>runstats.ingest]
    A --> I
    TB --> A
    I --> F1[FIT Files<br/>.fit]
    I --> F2[GPX Files<br/>.gpx]

    I --> M[Domain Model + Metrics<br/>runstats.models / runstats.metrics]
    M --> G[Reverse Geocoder<br/>runstats.geocode]
    G --> N[Nominatim Reverse API]
    G --> GC[Local Geocode Cache<br/>.runstats_geocode_cache.json]

    M --> T[Template Dispatcher<br/>runstats.templates]
    T --> TB[Basic Templates<br/>templates_basic.py]
    T --> TG[Glass Template<br/>templates_glass.py]
    T --> TC[Clipboard Template<br/>templates_clipboard.py]
    T --> TN[Neon Template<br/>templates_neon.py]

    TB --> R[Render Engine<br/>runstats.render + template_support]
    TG --> R
    TC --> R
    TN --> R

    R --> O[PNG Outputs<br/>exports/*.png]
    A --> AW[Automation Workspace<br/>C:\RunStatsAutomation]
    AW --> TGB
```

## Runtime Flow

1. A user runs `plot_gpx.py`, `runstats`, or one of the `.bat` helpers.
2. The CLI resolves the input activity file and output path.
3. `runstats.ingest` parses FIT/GPX data into `ActivityData`.
4. `runstats.metrics` computes summary stats and merges FIT summary hints when present.
5. If `--location` is not provided, `runstats.geocode` reverse geocodes the start coordinate and caches the result locally.
6. `runstats.templates` dispatches to the selected template module.
7. The renderer produces a transparent PNG in `exports/` or the explicitly requested output path.

Telegram automation flow:

1. A user sends a `.FIT` document to Telegram.
2. n8n downloads it into `C:\RunStatsAutomation\processing\`.
3. n8n runs `runstats-automation`.
4. The automation entrypoint reuses ingest, metrics, geocode, and templates, then writes JSON to stdout.
5. n8n sends the generated PNG back to Telegram and archives the FIT based on `status`.

Direct Telegram bot flow:

1. A user sends a `.FIT` document to the Telegram bot.
2. `runstats.telegram_bot` long-polls Telegram for updates.
3. The bot downloads the FIT into `C:\RunStatsAutomation\processing\`.
4. The bot calls `runstats-automation` logic in-process via `run_automation()`.
5. The bot replies with the generated PNG and archives the FIT based on `status`.

## Main Containers

- `CLI`: argument parsing, default paths, template choice, route mode, geocode trigger.
- `Automation`: machine-facing JSON command, workspace management, dedupe ledger, and caption assembly for n8n.
- `Telegram Bot Runner`: polling loop, Telegram file download/send, update offset persistence, and archive routing.
- `Ingest`: reads `.fit` / `.gpx` activity data and extracts track points plus Garmin session hints.
- `Models + Metrics`: immutable activity structures, cached derived arrays, pace/time/distance/elevation summary logic.
- `Geocoder`: optional location enrichment from start coordinates, with local JSON caching.
- `Templates`: visual layout modules for each overlay style.
- `Render Engine`: Matplotlib-based route plotting plus shared typography/figure helpers.
- `Outputs`: generated PNG overlays under `exports/`.

## Key Files

- [`plot_gpx.py`](/C:/Users/Eurus/Documents/GitHub/RunStats/plot_gpx.py)
- [`runstats/cli.py`](/C:/Users/Eurus/Documents/GitHub/RunStats/runstats/cli.py)
- [`runstats/automation.py`](/C:/Users/Eurus/Documents/GitHub/RunStats/runstats/automation.py)
- [`runstats/telegram_bot.py`](/C:/Users/Eurus/Documents/GitHub/RunStats/runstats/telegram_bot.py)
- [`runstats/ingest.py`](/C:/Users/Eurus/Documents/GitHub/RunStats/runstats/ingest.py)
- [`runstats/models.py`](/C:/Users/Eurus/Documents/GitHub/RunStats/runstats/models.py)
- [`runstats/metrics.py`](/C:/Users/Eurus/Documents/GitHub/RunStats/runstats/metrics.py)
- [`runstats/geocode.py`](/C:/Users/Eurus/Documents/GitHub/RunStats/runstats/geocode.py)
- [`runstats/templates.py`](/C:/Users/Eurus/Documents/GitHub/RunStats/runstats/templates.py)
- [`runstats/render.py`](/C:/Users/Eurus/Documents/GitHub/RunStats/runstats/render.py)
- [`runstats/template_support.py`](/C:/Users/Eurus/Documents/GitHub/RunStats/runstats/template_support.py)
