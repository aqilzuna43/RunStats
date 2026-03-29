# Telegram-Ingest FIT Automation

This repo now ships a machine-facing command for n8n and Telegram-driven ingestion:

```powershell
runstats-automation --input "C:\RunStatsAutomation\processing\123_ACTIVITY.fit"
```

The command always prints a single JSON object to stdout and creates the external automation workspace if it does not exist.

## Workspace

Default workspace root:

```text
C:\RunStatsAutomation
```

Created folders:

- `processing`
- `processed`
- `processed\duplicates`
- `failed`
- `failed\render`
- `failed\delivery`
- `exports`
- `logs`

Created files:

- `logs\processed_ledger.json`
- `logs\automation_events.jsonl`

## Command Contract

Example:

```powershell
runstats-automation `
  --input "C:\RunStatsAutomation\processing\22321337482_ACTIVITY.fit" `
  --workspace "C:\RunStatsAutomation" `
  --template glass_slab
```

Optional flags:

- `--output-dir "C:\RunStatsAutomation\exports"`
- `--location "Eco Horizon, Penang"`
- `--no-geocode`
- `--mode solid|gradient|auto`
- `--title "RELENTLESS"`
- `--no-title`

JSON shape:

```json
{
  "status": "success",
  "input_path": "C:\\RunStatsAutomation\\processing\\22321337482_ACTIVITY.fit",
  "sha256": "7d2c...",
  "template": "glass_slab",
  "output_path": "C:\\RunStatsAutomation\\exports\\glass_slab_22321337482_ACTIVITY.png",
  "distance_km": 10.04,
  "moving_time_s": 3291.0,
  "avg_pace_min_per_km": 5.46,
  "location": "Eco Horizon, Penang",
  "caption": "10.04 km | 54m 51s | 5:28 /km\nEco Horizon, Penang",
  "error": null
}
```

`status` values:

- `success`: render completed and the ledger was updated
- `duplicate`: the FIT hash already exists in the ledger, so rendering was skipped
- `error`: parsing, summary, or rendering failed; inspect `error`

## n8n Wiring

The recommended workflow is:

1. `Telegram Trigger`
2. Validate that the message is a document from your allowed chat/user and that the filename ends with `.fit`
3. Download the FIT file from Telegram into `C:\RunStatsAutomation\processing\`
4. `Execute Command`:

```powershell
runstats-automation --input "={{ $json.processingPath }}" --workspace "C:\RunStatsAutomation" --template glass_slab
```

5. Parse the JSON stdout
6. Branch by `status`

Success branch:

- Read `output_path` from disk
- Send the PNG back to the same Telegram chat with `caption`
- Move the FIT from `processing` to `processed`

Duplicate branch:

- Send a short "already processed" reply
- Move the FIT from `processing` to `processed\duplicates`

Error branch:

- Send a short failure reply
- Move the FIT from `processing` to `failed\render`

If the Telegram send step fails after rendering:

- Keep the PNG in `exports`
- Move the FIT from `processing` to `failed\delivery`

## Included Scaffold

A workflow scaffold is included at:

- [`n8n/telegram_ingest_workflow.example.json`](/C:/Users/Eurus/Documents/GitHub/RunStats/n8n/telegram_ingest_workflow.example.json)

Treat it as a starting point:

- bind your Telegram credential after import
- set your allowed Telegram chat/user ID
- confirm node option names against your installed n8n version
- keep `Execute Command` enabled on the self-hosted n8n instance
