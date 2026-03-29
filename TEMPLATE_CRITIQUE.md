# Template Critique & Improvement Roadmap

Samples reviewed from `exports/` using `20081725704_ACTIVITY.fit`.
Scores are subjective: **Visual** / **Data** / **Polish** out of 5.

---

## 1. `clean_card`

**Sample:** `clean_card_20081725704_ACTIVITY.png`
**Scores:** Visual 3/5 · Data 2/5 · Polish 3/5

### What Works
- Rainbow speed-colored route is the standout visual feature — immediately communicates effort variation.
- Rounded dark card on a transparent background is clean and versatile.
- Bold title ("RELENTLESS") gives personality at the top.

### Issues

| Severity | Issue |
|----------|-------|
| Medium | **Data poverty** — only 3 stats (Distance, Pace, Time). Heart rate, elevation, and calories are ignored even when present. |
| Medium | **Route feels small** — route axes are `[0.18, 0.38, 0.64, 0.34]` which leaves the title section and stats section feeling disconnected from the map. Route could expand to fill more of the card vertically. |
| Low | **No date or location** — every card should anchor the run in time and place. |
| Low | **Square canvas (1600×1600)** — larger than the other 1080px templates, making batch use inconsistent in file size and export time. |
| Low | **Label/value pair spacing** is hardcoded to 3 stat columns with fixed x-positions (0.20, 0.50, 0.80). Falls apart if fewer stats are available. |

### Suggested Improvements
- Add Date, Location pill, and optionally Heart Rate row below the 3-stat block.
- Increase route axes height to `~0.40` and shift stats block down to gain breathing room.
- Normalize canvas to 1080×1080 to match the other card templates.
- Make the stat columns adaptive (loop with evenly-spaced x positions based on count).

---

## 2. `glass_slab`

**Sample:** `glass_slab_20081725704_ACTIVITY.png`
**Scores:** Visual 2/5 · Data 1/5 · Polish 2/5

### What Works
- The frosted glass card concept (layered halo + fill + inner highlight + specular edge) is architecturally the most sophisticated of the four.
- Location pill at the bottom is well-sized and reads clearly.
- Start/end route markers (green/orange dots) are a nice touch.

### Issues

| Severity | Issue |
|----------|-------|
| **Critical** | **Stat values do not render.** The exported image shows only the labels (PACE, TIME, CAL, ELEV) and the "KM" unit label — the hero distance number and all four stat values are blank. The text is likely being drawn at positions that fall outside the figure bounds, or `font_props()` is returning a font that fails silently on this system. |
| High | **Glass effect is invisible on a white/light background.** The glass card uses `facecolor=(1,1,1,0.10)` — with a white canvas behind it, the card is indistinguishable from the background. The template needs either a background image, a dark canvas, or an opaque tinted background to make the glassmorphism visible. |
| Medium | **Route is a thin plain green line** — no speed coloring, no glow, no texture. Compared to `clean_card`'s rainbow route this reads as unfinished. |
| Low | **Hero font size (62pt) vs. unit label (24pt "KM")** — the "KM" is right-aligned to 0.86 while the number is centered at 0.5. This asymmetry looks accidental rather than designed. |
| Low | `font_props("semibold", 20)` used for stat values — `"semibold"` is not a standard matplotlib weight string; this silently falls back to default weight, undermining the intended hierarchy. |

### Suggested Improvements
- **Fix stat rendering first** — add a dark semi-transparent background (`#111111` at 80% alpha) to make both the glass card and the text visible.
- Replace the plain green line route with a speed-colored or glow variant.
- Align the "KM" unit label immediately to the right of the distance number rather than at a fixed x.
- Validate that `font_props` weight strings match matplotlib's accepted values (`"bold"`, `"heavy"`, `"light"`, `"normal"`).

---

## 3. `clipboard_card`

**Sample:** `clipboard_card_20081725704_ACTIVITY.png`
**Scores:** Visual 3/5 · Data 5/5 · Polish 4/5

### What Works
- Highest data density of all templates: 5 stat rows (Distance, Duration, Pace, Heart Rate, Elevation) with distinct geometric icons.
- Orange accent color is consistent and strong throughout (tab, border, header, icon backgrounds).
- Date and location in the header band anchor the run immediately.
- Dashed divider cleanly separates the hero distance from the detail rows.
- The "clipboard" tab concept (rounded tab + squared top-left corner) is a clever visual metaphor.

### Issues

| Severity | Issue |
|----------|-------|
| High | **No route map.** This is the only template with zero visual representation of the route. A small route thumbnail in the top-right of the white card area would dramatically improve visual appeal. |
| Medium | **Geometric icons are too small** (0.018 figure units) and drawn with thin lines — at export resolution they look like faint ticks rather than recognizable symbols. |
| Medium | The top-left corner "squaring" hack (two overlapping rectangles + a fill patch) is fragile — the white fill patch can leave a visible gap when the card background is not perfectly white. Consider using a clipping path instead. |
| Low | **`Heart Rate` row shows `145 bpm`** — the label field is `"Heart Rate"` (mixed case, two words) while all others are single-word (`"Distance"`, `"Duration"`). Inconsistent capitalization style. |
| Low | Distance is listed both as the hero stat and as the first detail row — this is **redundant**. The first row could be replaced with Calories or a run type label. |

### Suggested Improvements
- Add a small route minimap in the upper-right quadrant of the white card body (axes around `[0.55, 0.65, 0.38, 0.20]`).
- Increase icon size to 0.024–0.028 and use slightly heavier strokes.
- Remove the Distance detail row (it duplicates the hero) and replace with Calories.
- Normalize label casing: either ALL CAPS or Title Case across all rows.

---

## 4. `neon_split`

**Sample:** `neon_split_20081725704_ACTIVITY.png`
**Scores:** Visual 5/5 · Data 4/5 · Polish 3/5

### What Works
- Strongest visual identity of the four — the gradient orange bar against the near-black background is striking and immediately readable.
- Hero distance number is large, white, and dominant.
- Gradient orange→pink bar cleanly separates pace and duration into a single highlighted block.
- Mini route map in the top-right corner is a nice complement to the large number.
- Bottom grid (Calories / Heart Rate / Elevation) with dividers is well-spaced.

### Issues

| Severity | Issue |
|----------|-------|
| High | **"MORNING RUN" is hardcoded** — the label is always `"MORNING RUN"` regardless of the actual time of day or activity type. Should derive from the activity timestamp (Morning / Afternoon / Evening / Night Run) or from the activity's sport type if available. |
| Medium | **Footer is nearly invisible** — date and location use `alpha=0.20` which renders as light grey on dark grey. This is too faint to read comfortably. Recommended alpha: 0.45–0.55. |
| Medium | **"km" x-position is brittle** — the unit label is positioned at `0.085 + len(num_str) * 0.064`. This is a character-count hack that breaks when the distance changes digit count (e.g., `9.5` vs `13.30` vs `105.0`). Use a Text bounding box query or place "km" at a fixed offset relative to the number's right edge. |
| Low | The orange radial glow (`cx_frac=1.0, cy_frac=0.0`) originates from the top-right corner — the same area where the mini route map is rendered. The glow washes out the route's orange line, making it hard to read. Shift glow center slightly further off-canvas or reduce `peak_alpha` to 0.15. |
| Low | Bottom-grid label alpha (`0.25`) is very faint — values are legible but labels are borderline. Increase to 0.45 for better scannability. |
| Low | Column divider lines use `alpha=0.12` — barely visible. Increase to 0.20–0.25. |

### Suggested Improvements
- Replace `"MORNING RUN"` with a dynamic time-of-day derivation from `activity.start_time`.
- Increase footer alpha to 0.50 and bottom label alpha to 0.45.
- Replace the character-count km-position hack with `fig.text(...).get_window_extent()` or a two-call layout approach.
- Offset the radial glow origin to `cx_frac=1.10` to push it further into the corner and away from the route.

---

## 5. `story_overlay`

**Sample:** `story_overlay_20081725704_ACTIVITY.png`
**Scores:** Visual 2/5 · Data 1/5 · Polish 1/5

### What Works
- Portrait canvas (1080×1920) is correctly sized for Instagram Stories.
- The large orange route dominates the frame appropriately for the format.
- The code path correctly handles the no-route and no-summary edge cases.

### Issues

| Severity | Issue |
|----------|-------|
| **Critical** | **Stats are not rendering.** The exported image shows only the route and the orange separator line — Distance, Pace, and Time values are completely absent. The text is likely white on a white canvas (the background is `#FFFFFF` by default and the text `color` inherits from `style.text_color`). |
| High | **No visual identity** — white background with an orange line feels like a wireframe, not a finished product. The template needs either a background color, a photo placeholder, or at minimum a brand element. |
| High | **Only 3 stats** — the same data limitation as `clean_card`. The story format has ample vertical space for 5–6 stats plus a location footer. |
| Medium | **`add_stat_row` positions are hardcoded** (`0.38`, `0.27`, `0.16`) with a separator at `0.47`. If the title is long or the route is tall, these overlap with the route axes. |
| Low | No date, no location, no branding — the story overlay is the highest-reach format (full-screen on Stories) but carries the least information. |

### Suggested Improvements
- **Fix text visibility first** — set the canvas background to a dark color (e.g., `#111111`) or ensure `style.text_color` is set to something visible against the actual background.
- Add a subtle background gradient or dark overlay so the template reads as finished.
- Expand stat coverage to include Heart Rate and Elevation.
- Add date and location at the bottom of the canvas in small, faded text.
- Consider making the route color-coded by speed (same as `clean_card`) to leverage the larger canvas.

---

## Cross-Template Summary

| Template | Route | Data Richness | Visual Identity | Critical Bugs |
|----------|-------|---------------|-----------------|---------------|
| `clean_card` | Rainbow speed-colored | Low (3 stats) | Good | None |
| `glass_slab` | Plain green line | None (values blank) | Weak (invisible glass) | Stats not rendering |
| `clipboard_card` | None | High (5 stats) | Good | None |
| `neon_split` | Mini orange line | Medium (6 fields) | Excellent | None |
| `story_overlay` | Large orange line | None (values blank) | Minimal | Stats not rendering |

### Top Priorities Across All Templates

1. **Fix `glass_slab` and `story_overlay`** — stats not rendering makes both templates unusable.
2. **Add a route to `clipboard_card`** — it is the most data-rich template but has no visual map.
3. **Fix the `"MORNING RUN"` hardcode in `neon_split`** — easy win, high visibility.
4. **Add dark backgrounds** to `glass_slab` and `story_overlay` — both are invisible on white.
5. **Increase `neon_split` footer and label alphas** — readability improvement with minimal effort.
