# High-Performance Fitness Overlay Design System

## 1. Overview & Creative North Star
**Creative North Star: The Kinetic Editorial**

This design system is engineered to transform raw athletic data into a premium, gallery-ready narrative for Instagram Stories. Unlike generic fitness trackers that clutter the screen with heavy boxes and rigid grids, this system treats the user’s photo or video as the primary canvas. 

We move beyond the "app" look toward a "luxury editorial" feel. We achieve this through **Kinetic Asymmetry**—placing key metrics with intentional breathing room and utilizing overlapping glass layers that feel like physical artifacts floating over the content. The layout is high-performance: thin, razor-sharp typography for labels contrasted against massive, brutalist display values for core stats.

## 2. Colors
Our palette is rooted in a deep, nocturnal base to allow vibrant performance accents to "pop" with maximum luminance.

*   **Primary Accent (`#f3ffca`):** This is our "Electric Lime." It is used for primary distance metrics and success states. 
*   **Secondary Accent (`#ff734a`):** Our "Kinetic Orange," reserved for high-intensity data points like pace or elevation spikes.
*   **Surface Logic:** We use `surface` (#0e0e0e) at varying opacities to create depth.
*   **The "No-Line" Rule:** 1px solid borders are strictly prohibited for sectioning. Structural boundaries must be defined solely through background color shifts (e.g., a `surface-container-low` component sitting on a `surface` background).
*   **Surface Hierarchy & Nesting:** Use `surface-container` tiers to create "stacked" depth. A metric card should use `surface-container-highest` with a backdrop blur to separate it from the photo background.
*   **The "Glass & Gradient" Rule:** All primary overlay containers must utilize **Glassmorphism**. Apply a `surface-variant` color at 40-60% opacity with a `20px` to `40px` backdrop-blur. 
*   **Signature Textures:** For hero stats, use a subtle linear gradient transitioning from `primary` (#f3ffca) to `primary-container` (#cafd00) to give the text a metallic, high-end sheen.

## 3. Typography
The typographic system uses a high-contrast pairing of **Space Grotesk** for data-heavy "performance" moments and **Manrope** for "editorial" clarity.

*   **Display Large (Space Grotesk, 3.5rem):** Reserved for the "Hero Metric" (e.g., total distance). 
*   **Headline Small (Space Grotesk, 1.5rem):** Used for primary secondary stats like Pace or Heart Rate.
*   **Title Medium (Manrope, 1.125rem):** For location data or "Run Title."
*   **Label Small (Manrope, 0.6875rem):** Always uppercase with `0.1em` letter spacing. These identify the metric type (e.g., "CALORIES").
*   **Hierarchy Strategy:** The scale jump between `Label-sm` and `Display-lg` is intentional. It mimics high-end Swiss poster design, making the data feel authoritative and intentional.

## 4. Elevation & Depth
In a transparent overlay environment, depth is managed through **Tonal Layering** and optical physics rather than heavy shadows.

*   **The Layering Principle:** Stack `surface-container` tiers. For example, a `surface-container-low` map path should sit beneath a `surface-container-highest` stat card. 
*   **Ambient Shadows:** If a card requires a "lift" from a busy photo background, use an extra-diffused shadow: `0px 20px 40px rgba(0, 0, 0, 0.15)`. Never use high-opacity black shadows.
*   **The "Ghost Border":** If a container needs further definition, use the `outline-variant` token at **15% opacity**. This creates a "specular highlight" on the edge of the glass rather than a flat border.
*   **Glassmorphism & Depth:** To ensure legibility over highly detailed photos (e.g., a forest run), the `backdrop-blur` is your primary tool. The busier the background, the higher the blur value (up to `xl`/24px).

## 5. Components
Components are designed to be "lightweight" to avoid obscuring the user's content.

*   **Metric Cards:** Use `roundedness-lg` (1rem). Background must be semi-transparent glass. No dividers—use `spacing-4` (1.4rem) to separate columns of data.
*   **Data Chips:** Small, high-contrast pills using `primary` or `secondary` backgrounds with `on-primary` text. Use `roundedness-full`.
*   **The "Kinetic Path":** For maps, use a dashed line with `secondary` (#ff734a). The path should have a subtle outer glow (glow color: `secondary-dim`) to mimic an LED display.
*   **Location Header:** Always centered. Use `title-md` for the city name and `label-sm` for the date. 
*   **Progress Bars:** Ultra-thin (2px). Use `surface-variant` as the track and a gradient of `primary` to `primary-container` for the fill.

## 6. Do's and Don'ts

### Do
*   **DO** use whitespace as a separator. Use `spacing-6` (2rem) between major content blocks.
*   **DO** ensure text contrast. If a photo is too bright, increase the `surface-dim` overlay opacity behind the text.
*   **DO** center-align location and date at the very top or bottom of the screen to create an editorial "frame."
*   **DO** use icons sparingly. Icons should be `24px` and utilize the `outline` token weight.

### Don't
*   **DON'T** use 100% opaque black or white backgrounds for containers. It kills the "overlay" feel of a Story.
*   **DON'T** use traditional drop shadows with 0 blur.
*   **DON'T** use serif fonts. This system is strictly high-performance, precision-engineered sans-serif.
*   **DON'T** use more than two accent colors in a single screen. Stick to `Primary` (Lime) for "Go/Success" and `Secondary` (Orange) for "Intensity/Warning."