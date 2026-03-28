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

Render the Instagram Story overlay directly:

```bash
python plot_gpx.py --input 21760678383_ACTIVITY.fit --template story_overlay --output story_overlay.png
```

Render the alternate card layout:

```bash
python plot_gpx.py --input activity.gpx --template clean_card --output clean_card.png
```

If timing data is missing and you still want the route art:

```bash
python plot_gpx.py --input activity.gpx --route-only --output route_only.png
```

## Templates

- `story_overlay`: transparent 1080x1920 Instagram Story-style overlay
- `clean_card`: alternate square card layout

## Useful flags

- `--mode solid|gradient|auto`
- `--title "MORNING RUN"`
- `--no-title`
- `--auto`
- `--search-dir .`
