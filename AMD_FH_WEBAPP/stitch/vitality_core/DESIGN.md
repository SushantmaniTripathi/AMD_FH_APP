# Design System Specification: The Clinical Epicurean

## 1. Overview & Creative North Star
This design system is built at the intersection of medical precision and gastronomic delight. We are moving away from the "utility-first" look of standard delivery apps toward a **"High-End Digital Editorial"** experience. 

**Creative North Star: The Clinical Epicurean.**
The system must feel like a premium wellness concierge. We achieve this by breaking the rigid, boxed-in layouts of traditional e-commerce. Instead, we utilize **intentional asymmetry**, overlapping elements that break container boundaries, and a sophisticated hierarchy of "surfaces" rather than lines. This approach signals intelligence and trustworthiness while remaining vibrant and appetizing.

---

## 2. Color & Surface Philosophy
The palette balances the sterile trust of health-tech with the warmth of food culture.

### Color Mapping
- **Primary (`#00685c`):** Our Vibrant Teal. Used for clinical trust, tech-forward actions, and health-affirmation.
- **Secondary (`#984800`):** The "Familiar Orange." Reserved for appetite-driven actions, delivery status, and food-centric highlights.
- **Tertiary (`#006b1b`):** The Leaf Green. Strictly for high-performance health scores and positive nutritional data.
- **Error (`#ba1a1a`):** The Muted Coral. Used for "unhealthy nudges" or warnings, designed to be informative rather than alarming.

### The "No-Line" Rule
**Explicit Instruction:** Designers are prohibited from using 1px solid borders for sectioning or card definition. Boundaries must be defined solely through:
1. **Background Color Shifts:** Use `surface-container-low` for the main canvas and `surface-container-lowest` (Pure White) for elevated content cards.
2. **Tonal Transitions:** A subtle shift from `surface` to `surface-variant` creates a natural break without visual clutter.

### Surface Hierarchy & Nesting
Treat the UI as a physical stack of premium materials—frosted glass and heavy-weight paper.
- **Base:** `surface` (#f8f9fa).
- **Lower Level:** `surface-container-low` for subtle grouping of background elements.
- **Interactive Layer:** `surface-container-lowest` (#ffffff) for primary cards to create a "lift" effect.
- **Signature Textures:** For high-impact CTAs, use a subtle linear gradient transitioning from `primary` to `primary_container`. This adds a "lithographic" depth that flat hex codes lack.

---

## 3. Typography: The Technical Editorial
We utilize a pairing of **Manrope** for authoritative displays and **Inter** for functional clarity.

- **Display & Headlines (Manrope):** Use `display-lg` and `headline-lg` to create editorial impact. Ensure letter-spacing is set to `-0.02em` for large headlines to maintain a premium, "tight" feel.
- **Body & Labels (Inter):** Use `body-md` for general content. The high x-height of Inter ensures legibility even when layered over complex food photography.
- **Hierarchy as Brand:** Use `title-lg` in `primary` teal to denote "Healthy Insights," while using `title-lg` in `on_surface` for "Menu Items." This subtle color-coding in typography guides the user’s intent.

---

## 4. Elevation & Depth
Depth is achieved through **Tonal Layering**, not structural scaffolding.

### The Layering Principle
Stacking surface tiers creates a soft, natural lift. Place a `surface-container-lowest` card on a `surface-container-low` section to define a container. 

### Ambient Shadows
When a "floating" effect is required (e.g., a bottom navigation bar or a floating cart), use **Ambient Shadows**:
- **Blur:** 24px to 40px.
- **Opacity:** 4%–8%.
- **Color:** Instead of pure black, use a tinted version of `on-surface` (#191c1d) to mimic natural light.

### Glassmorphism & Ghost Borders
- **Glass Overlays:** For context overlays (modals/filters), use a `surface` color at 70% opacity with a `20px` backdrop-blur. This keeps the user connected to the food imagery behind the UI.
- **The "Ghost Border":** If a boundary is essential for accessibility, use the `outline-variant` token at **15% opacity**. Never use 100% opaque borders.

---

## 5. Components

### Buttons: The Tactile Touchpoints
- **Primary:** High-pill shape (`rounded-full`). Background: `primary` to `primary_container` gradient. Typography: `label-md` in `on_primary`.
- **Secondary:** `surface-container-highest` background with `on_surface` text. No border.
- **States:** On press, apply a 10% black overlay to the gradient to simulate physical depression.

### Cards: The Content Vessels
- **Radius:** Strictly `1.5rem` (xl). 
- **Structure:** Forbid the use of divider lines. Use `body-sm` in `on_surface_variant` to create headers, and use vertical white space (24px) to separate the image from the description.
- **Contextual Glass:** Nutrition "Quick-Stats" should be rendered as small glassmorphic chips floating over the food photography.

### Input Fields: Minimalist Tech
- **Style:** Understated. Use `surface-container-low` as the fill color. 
- **Focus State:** Transition the background to `surface-container-lowest` and add a `2px` "Ghost Border" of `primary` at 40% opacity. 

### Custom Health-Tech Components
- **The Score-Gauge:** A custom circular progress component using `tertiary` (Leaf Green) for high scores. The center of the gauge should use glassmorphism to show the underlying background.
- **The Nudge-Bar:** A slim, `surface-container-high` bar at the top of the menu with a `Muted Coral` (error) icon to subtly inform users of high-sodium or allergen content.

---

## 6. Do’s and Don’ts

### Do:
- **Use White Space as a Luxury:** Give elements twice as much room as you think they need. Space is a sign of a premium experience.
- **Overlap Elements:** Let a high-quality dish image break out of its card and overlap a headline to create a 3D, "magazine" feel.
- **Respect the Tones:** Use the `surface-container` tiers precisely. Mixing them randomly will break the illusion of depth.

### Don’t:
- **No Heavy Shadows:** Avoid "drop shadows" that look like 2010-era UI. If you can see the shadow clearly, it’s too dark.
- **No Hard Dividers:** Never use a solid line to separate two pieces of content. If they need to be separate, use a background color shift or a `32px` gap.
- **No Default Grids:** Avoid placing every card in a perfectly even 2-column grid. Vary the widths (e.g., a 60/40 split) to keep the user engaged.

---

**Director’s Final Note:** 
This system should feel like a bridge between a high-end medical lab and a Michelin-star kitchen. It is clean but never cold; vibrant but never chaotic. Follow the tokens, but lead with your eyes.