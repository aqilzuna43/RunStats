# Design System Specification: High-Performance Sports Data Visualization

## 1. Overview & Creative North Star: "The Kinetic Pulse"
The Creative North Star for this design system is **"The Kinetic Pulse."** In the world of high-performance sports, data is not static; it is a living, breathing representation of human limit-pushing. This system moves away from the "static dashboard" trope and toward a high-end, editorial cockpit experience.

By utilizing **intentional asymmetry**—such as placing heavy data visualizations against oversized, minimalist display typography—we create a sense of forward motion. We break the "template" look by layering frosted surfaces over deep obsidian voids, creating a sense of infinite depth. The goal is to make the user feel like they are looking through a high-tech lens at a live event, where every pixel is tuned for speed and precision.

---

## 2. Colors: Obsidian & Electric Light
The palette is built on a foundation of absolute darkness to allow the high-frequency "Electric Orange" to vibrate with maximum intensity.

### Color Tokens
- **Background (Obsidian):** `#000000` (Surface-Container-Lowest).
- **Primary (Electric Orange):** `#FF8F6F` (Active states, critical data peaks).
- **On-Primary:** `#5C1400` (Contrast text on orange).
- **Secondary (Cool Silver):** `#E2E2E2` (Supporting UI elements).
- **Surface Tiers:**
  - `Surface-Container-Low`: `#131313`
  - `Surface-Container-High`: `#1F1F1F`
  - `Surface-Variant`: `#262626`

### The "No-Line" Rule
Standard 1px solid borders for sectioning are strictly prohibited. Boundaries must be defined solely through background color shifts. For example, a `surface-container-high` data module should sit directly on a `surface` background. The transition in tone is the divider.

### The "Glass & Gradient" Rule
To elevate the "Electric Orange" from a flat hex code to a premium material, utilize linear gradients. Use a transition from `primary` (#FF8F6F) to `primary-container` (#FF7851) at a 135-degree angle for main CTAs. This provides a "glow" effect that mimics stadium lighting.

---

## 3. Typography: Technical Authority
We pair the brutalist geometry of **Space Grotesk** for displays with the hyper-legibility of **Inter** for data.

- **Display (Space Grotesk):** Used for scores, high-level metrics, and hero titles. It conveys a "technical editorial" feel.
- **Body & Labels (Inter):** Used for all analytical text. Inter’s tall x-height ensures readability during fast-paced data updates.

| Level | Token | Font | Size | Case |
| :--- | :--- | :--- | :--- | :--- |
| **Hero Metric** | `display-lg` | Space Grotesk | 3.5rem | Bold |
| **Section Head** | `headline-sm` | Space Grotesk | 1.5rem | Medium |
| **Data Label** | `label-md` | Inter | 0.75rem | All Caps (0.05em tracking) |
| **Reading** | `body-md` | Inter | 0.875rem | Regular |

---

## 4. Elevation & Depth: Tonal Layering
In this system, depth is not simulated with shadows; it is built with light and transparency.

### The Layering Principle
Depth is achieved by stacking surface tiers.
1. **Base:** `surface` (#0E0E0E)
2. **Mid-Level:** `surface-container-low` (#131313)
3. **Interactive:** `surface-container-high` (#1F1F1F)

### Glassmorphism & Depth
For floating overlays (e.g., player stats cards), use a "Frosted Obsidian" effect:
- **Fill:** `surface-variant` at 20% opacity.
- **Backdrop Blur:** 12px to 20px.
- **The "Ghost Border":** A 1px stroke using `outline-variant` at 15% opacity. This provides a "shimmer" edge without creating a hard structural box.

### Ambient Shadows
Standard drop shadows are replaced by "Glow Shadows." When a card is active, apply a diffused shadow using a 4% opacity version of the `primary` (Electric Orange) color. This mimics the way an LED screen casts light on a dark surface.

---

## 5. Components: Precision Engineered

### Buttons
- **Primary:** Gradient fill (`primary` to `primary-container`), no border, `md` (0.375rem) corner radius. Text is `on-primary`.
- **Secondary:** Ghost style. `outline-variant` (20% opacity) border with `on-surface` text.
- **Tertiary:** Pure text using `primary` color, no container.

### Data Cards
Forbid the use of divider lines. Use vertical white space (`spacing-8` or `spacing-10`) to separate athlete stats.
- **Background:** `surface-container-low`.
- **Edge:** 1px "Ghost Border" at the top edge only to catch "light."

### Inputs & Search
- **Field:** `surface-container-highest` background.
- **Focus State:** No thick border. Instead, change the background to `surface-bright` and shift the label color to `primary`.

### Performance Chips
- **Status:** Use `error_dim` (#D7383B) for live/hot status and `secondary` for inactive. Use a 2px pulse animation for "Live" indicators.

---

## 6. Do's and Don'ts

### Do
- **DO** use the `0.2rem` (1) and `0.4rem` (2) spacing increments for tight data clusters to maintain a "technical" density.
- **DO** use `Space Grotesk` for numbers. Numeric data is the "hero" of this system.
- **DO** leverage `surface-container-lowest` (#000000) for the most recessed areas of the UI to create maximum contrast with data visualizations.

### Don't
- **DON'T** use 100% white (#FFFFFF) for long-form body text; use `secondary` (#E2E2E2) to reduce eye strain against the black background.
- **DON'T** use rounded corners larger than `xl` (0.75rem). This system is precision-based; overly round "pill" shapes feel too consumer-soft.
- **DON'T** use standard Material shadows. If it doesn't look like it's glowing or refracting light, it doesn't belong in this system.