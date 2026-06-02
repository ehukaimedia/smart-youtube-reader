---
name: Smart YouTube Reader
description: Dark, work-focused operator UI for turning YouTube into AI-readable learning archives.
colors:
  background: "#050505"
  surface: "#0f1115"
  surface-raised: "#171b22"
  border: "#1f242c"
  border-strong: "#29303a"
  text: "#f4f7fb"
  text-muted: "#9aa4b2"
  accent: "#3b82f6"
  accent-deep: "#2563eb"
  success: "#10b981"
  success-deep: "#0e8a6c"
  warn: "#f59e0b"
  error: "#ef4444"
  badge-success-bg: "#102918"
  badge-success-border: "#256d3b"
typography:
  display:
    fontFamily: "Inter, system-ui, Segoe UI, sans-serif"
    fontSize: "clamp(1.75rem, 2.6vw, 2.25rem)"
    fontWeight: 700
    lineHeight: 1.1
    letterSpacing: "-0.01em"
  headline:
    fontFamily: "Inter, sans-serif"
    fontSize: "1.25rem"
    fontWeight: 600
    lineHeight: 1.25
    letterSpacing: "normal"
  title:
    fontFamily: "Inter, sans-serif"
    fontSize: "1rem"
    fontWeight: 600
    lineHeight: 1.35
    letterSpacing: "normal"
  body:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.95rem"
    fontWeight: 400
    lineHeight: 1.55
    letterSpacing: "normal"
  label:
    fontFamily: "Inter, sans-serif"
    fontSize: "0.75rem"
    fontWeight: 600
    lineHeight: 1.2
    letterSpacing: "0.08em"
  mono:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, Consolas, monospace"
    fontSize: "0.85rem"
    fontWeight: 400
    lineHeight: 1.45
    letterSpacing: "normal"
rounded:
  sm: "6px"
  md: "8px"
  lg: "12px"
  pill: "999px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "16px"
  lg: "24px"
  xl: "32px"
components:
  button-primary:
    backgroundColor: "{colors.accent}"
    textColor: "#061016"
    rounded: "{rounded.md}"
    padding: "8px 14px"
  button-primary-hover:
    backgroundColor: "{colors.accent-deep}"
    textColor: "#061016"
  button-secondary:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "8px 14px"
  button-success:
    backgroundColor: "{colors.success}"
    textColor: "#061a13"
    rounded: "{rounded.md}"
    padding: "8px 14px"
  icon-button:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.text-muted}"
    rounded: "{rounded.md}"
    size: "36px"
    height: "36px"
    width: "36px"
  input-text:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "10px 12px"
  chip:
    backgroundColor: "{colors.surface-raised}"
    textColor: "{colors.text-muted}"
    rounded: "{rounded.pill}"
    padding: "3px 8px"
  chip-active:
    backgroundColor: "{colors.badge-success-bg}"
    textColor: "{colors.success}"
    rounded: "{rounded.pill}"
  card:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.text}"
    rounded: "{rounded.md}"
    padding: "14px"
imagery:
  northStar: "inspired visual learning"
  theme: "concept-led visual system, adapted per digest and held coherent across all images"
  canvasLight: "#ffffff or #f5f5f7"
  canvasDark: "#000000 to #101012"
  headlineLight: "#1d1d1f"
  headlineDark: "#f5f5f7"
  bodyLight: "#6e6e73"
  bodyDark: "#a1a1a6"
  accent: "Operator Blue #3b82f6 fill, #2563eb text"
  accentRule: "premium images may use full color when it teaches; color must be intentional, never arbitrary"
  font: "Inter, Helvetica Neue, or the system UI sans, never a default serif"
  elevation: "flat, subtle shadow only under a real product photo, never decorative"
  craft: "generous whitespace, precise alignment, one idea per card"
  format: "webp"
  aspectRatio: "16:9"
  pixelSize: "1600x900"
  maxImagesPerDigest: 6
  oneIdeaPerImage: true
---

# Design System: Smart YouTube Reader

## 1. Overview

**Creative North Star: "The Operator's Library at Night"**

This is a working library, used by one person, late, in a dim room, on a dark monitor with several other tools open. The surface should disappear and let the artifacts (titles, chapters, frames, archives) lead. Density is welcome; clutter is not. The reading experience is closer to a long-form notes app than to a video product, because the artifact the operator consumes is text and structured chapters, not the video itself.

The system explicitly rejects the SaaS aesthetic vocabulary: no hero gradients, no marketing flourish, no animated illustrations, no glassmorphism reflex, no gradient text headlines. Where the existing codebase has these (`.glass-card`, `.title-gradient`), they are legacy debt; new work uses tinted neutrals and flat surfaces and earns hierarchy through weight and size.

**Key Characteristics:**
- Near-black background with neutrals tinted toward the accent hue, never pure `#000`.
- One accent (blue), used sparingly — primary buttons, active states, focus rings.
- Success green and error red carry status; both have a low-saturation tinted background variant for badges.
- Type at body size is 0.95rem with 1.55 line-height, capped at 72ch for reading.
- Surfaces are flat by default. Elevation comes from a 1px border tint, not from shadow.

## 2. Colors

A near-monochrome dark palette with one cool-blue accent. Status is carried by green and red; everything else is graded neutrals.

### Primary

- **Operator Blue** (`#3b82f6`): the single accent. Primary buttons, active nav state, focus rings, the slicer's selected timeline range. No decorative use.
- **Operator Blue Deep** (`#2563eb`): hover and pressed state for primary buttons.

### Secondary

- **Working Green** (`#10b981`): success state on group-digest CTAs, "Selected" toggles, completion badges paired with `Badge Green Bg`.
- **Caution Amber** (`#f59e0b`): reserved for in-flight processing chips. Use sparingly; never as a button color.
- **Stop Red** (`#ef4444`): destructive confirmation, failed status, image-removal warnings. Never used as an accent for emphasis.

### Neutral

- **Background Coal** (`#050505`): the page surface. Never `#000`.
- **Surface Slate** (`#0f1115`): cards, panels, the article column background.
- **Surface Slate Raised** (`#171b22`): toolbar pills, icon buttons, input fields.
- **Border Quiet** (`#1f242c`): default 1px border on cards and inputs at rest.
- **Border Strong** (`#29303a`): hover and focus border, keyboard-visible focus ring.
- **Text Primary** (`#f4f7fb`): body and headings on dark surfaces.
- **Text Muted** (`#9aa4b2`): captions, dates, "subtle" labels, inactive nav items.

### Named Rules

**The One Accent Rule.** Operator Blue appears on ≤10% of any given screen. The primary button, the active step, the focused field, the highlighted chapter row — that is the budget. If a third blue surface would appear, demote one of the existing two to neutral.

**The Tinted Neutral Rule.** Never use `#000` or `#fff`. Every neutral carries a faint cool tint so the palette holds together. The text muted token is `#9aa4b2`, not `#999999`.

## 3. Typography

**Display Font:** Inter (with `system-ui, Segoe UI, sans-serif` fallback)
**Body Font:** Inter
**Label/Mono Font:** `ui-monospace, SFMono-Regular, Menlo, Consolas, monospace` (for textarea prompt content and raw JSON only)

**Character:** A single sans family doing the entire job. Hierarchy comes from weight (400 / 600 / 700) and size, with letter-spacing reserved for small-caps labels. The pairing is technical and quiet; nothing decorative.

### Hierarchy

- **Display** (700, clamp 1.75rem–2.25rem, 1.1 line-height): page title, e.g. "Learning library", "Choose teaching frames". One per screen.
- **Headline** (600, 1.25rem, 1.25 line-height): card titles, panel headings, chapter concept names.
- **Title** (600, 1rem, 1.35 line-height): action bar headings, badge groups, slicer step labels.
- **Body** (400, 0.95rem, 1.55 line-height, **cap at 72ch**): article paragraphs in the reader, descriptive paragraphs in panels.
- **Label** (600, 0.75rem, 0.08em letter-spacing, uppercase): sidebar section headings ("PRESETS", "SCREEN"), small captions over inputs.
- **Mono** (400, 0.85rem, 1.45 line-height): the implementation-prompt textarea, raw transcript timestamps, JSON paths in CLI prompts.

### Named Rules

**The 72ch Rule.** Article body text is capped at 72 characters per line. Full-viewport-width paragraphs are treated as a defect, not a tradeoff.

**The No-Gradient-Text Rule.** Headlines use solid color and weight contrast. `background-clip: text` over a gradient is prohibited; the existing `.title-gradient` class is on retirement watch.

## 4. Elevation

Flat by default. Depth is signaled by a 1px border tint shift and a small surface-color step, not by shadow. The system has no ambient drop shadow vocabulary; the one acceptable shadow is a subtle preview frame around the playground canvas to suggest "this is a sample, not the live app."

### Shadow Vocabulary

- **Frame Drop** (`box-shadow: 0 18px 60px rgba(0,0,0,0.35)`): used only on the playground preview frame to set it apart from the page background. Not for general components.

### Named Rules

**The Flat-By-Default Rule.** Cards, panels, dropdowns, popovers, and modals carry no shadow at rest. Depth comes from `Border Quiet → Border Strong` and `Surface Slate → Surface Slate Raised` step changes.

**The No-Glow Rule.** The legacy `--primary-glow` rgba and the `box-shadow` glow on `.btn:hover` are retired. Primary button hover transitions only the background color from Operator Blue to Operator Blue Deep.

## 5. Components

### Buttons

- **Shape:** Gently squared corners (`{rounded.md}`, 8px).
- **Primary:** Operator Blue background, dark text (`#061016`), 8px 14px padding, 36px minimum height. Hover transitions background to Operator Blue Deep with no glow. Used for the single hero action on each surface (`Open Project`, `New Project`, `Copy Learning Prompt`).
- **Secondary:** Surface Slate Raised background, Text Primary, 1px Border Quiet. Used for non-hero actions in the action bar (`Copy Project Link`, `Open Slicer`).
- **Success:** Working Green background, near-black text. Used only on group-digest CTAs and "Save to project" — actions that produce a new artifact.
- **Danger:** Surface Slate Raised background, Stop Red text, 1px tinted red border. Confirmation-only; never primary on any surface.
- **Icon button:** 36×36px, Surface Slate Raised, Text Muted icon, hover lifts the icon to Text Primary. Always carries `aria-label`. Used for `⋯` overflow triggers, dismiss `×`, and inline copy/download icons.
- **Hover / Focus:** Background color change only on hover. On focus-visible, Border Strong appears as a ring. No `outline: none` without a replacement.

### Chips

- **Style:** Surface Slate Raised background, Text Muted text, 1px Border Quiet, pill radius. Compact (3px 8px padding, 0.75rem text).
- **Status variant** (success): Badge Success Bg (`#102918`) + Working Green text + Badge Success Border. Used for `complete`, `Grouped`, `Selected`.
- **Filter variant** (toolbar): same neutral chip with an `active` state that swaps border to Operator Blue and background to a 18%-mixed accent tint. Used for the dashboard status filter (All / Complete / Processing / Failed).

### Cards / Containers

- **Corner Style:** `{rounded.md}` (8px). The legacy `.glass-card` at 16px radius is on retirement watch; new cards use 8px.
- **Background:** Surface Slate. No translucency, no backdrop blur.
- **Shadow Strategy:** None. See Elevation.
- **Border:** 1px Border Quiet at rest. Hover or selected state shifts to Border Strong.
- **Internal Padding:** 14px (`{spacing.md}` minus a tick) for project cards; 16px for panels; 24px for the page content area.

### Inputs / Fields

- **Style:** Surface Slate Raised, 1px Border Quiet, 8px radius, 10px 12px padding.
- **Focus:** Border shifts to Operator Blue, no outer glow.
- **Search input:** carries `type="search"`, full width of its column, no inline button. A search input is an input, never a button labeled "Search".
- **Error / Disabled:** disabled opacity 0.5, cursor not-allowed; error state borders shift to Stop Red.

### Navigation

- **Top nav (current app pattern):** flat top bar, brand wordmark on the left, route links on the right ("New Project", "Dashboard"). Active route uses Text Primary against Surface Slate Raised pill; inactive uses Text Muted.
- **Typography:** Title (600, 1rem). No uppercase, no letter-spacing.
- **No sidebar nav.** With three routes total (Dashboard / Reader / Slicer), a sidebar is more chrome than the app earns. The playground's sidebar variant is decoration, not direction.

### Action Bar (signature component)

A horizontal bar of buttons that sits beneath a page title, holding one primary action and up to three secondary actions plus a `⋯` overflow. Used on the Reader and the Slicer review state. Replaces the current pattern of "stuff all six actions into the page header." Spec:

- Primary button on the left, secondary buttons to its right, overflow `⋯` on the far right.
- Buttons do not wrap to a second row; if they would, the lowest-priority secondary action moves into the overflow menu instead.
- The overflow menu is a popover, not a modal; opens on click and keyboard-focus, dismisses on outside click or `Esc`.

### Card (Project)

- Thumbnail (16:9, video frame or YouTube hqdefault), status + kind badges row, headline (card title), muted caption (date), one primary `Open Project` button, one icon-button `⋯` overflow holding `Copy Link`, `Download ZIP`, `Add to Group`, `Delete`.
- The Tailscale URL is **never** rendered as inline text on the card.
- Selection state for grouping: the `⋯` overflow item toggles to `Selected`, the card border shifts to Operator Blue, and a `Grouped` chip appears in the badge row.

## 6. Do's and Don'ts

### Do:

- **Do** cap article body text at 72ch.
- **Do** use Operator Blue (`#3b82f6`) as the single accent. Hover transitions to Operator Blue Deep (`#2563eb`) with no glow.
- **Do** render the group-digest bar only when one or more projects are selected.
- **Do** consolidate secondary actions into a `⋯` overflow menu on cards and headers. One primary, the rest hidden.
- **Do** label icon-only buttons with `aria-label` or `title` text.
- **Do** use solid colors with weight contrast for hierarchy.
- **Do** preserve existing handlers (copy, download, share, group, delete, slicer routing) when refactoring presentation. Behavior is stable; the surface gets calmer.
- **Do** show real project titles, real chapter names, and real stats in any preview, mock, or playground. Lorem ipsum is a defect.

### Don't:

- **Don't** print the Tailscale URL inline on dashboard cards. Keep the action; hide the URL string.
- **Don't** use `background-clip: text` over a gradient. `.title-gradient` is a legacy class; do not extend it.
- **Don't** wrap new cards in `.glass-card`. The blur + translucent fill aesthetic is legacy; new cards are Surface Slate with a 1px border.
- **Don't** add `box-shadow` for ambient depth. Flat-by-default.
- **Don't** introduce sidebar navigation for three routes.
- **Don't** render the always-visible group bar with `(0)` selected. Conditional UI only.
- **Don't** ship five equally-weighted buttons in a page header. One primary, the rest in an action bar or overflow.
- **Don't** use `outline: none` on focusable elements without a visible replacement.
- **Don't** use modal dialogs for confirmations that work as toasts.
- **Don't** copy the visual language of other well-known productivity apps. This product is its own register.
- **Don't** use `#000` or `#fff`. Every neutral is tinted.
- **Don't** use em dashes in UI copy or labels. Commas, colons, semicolons, periods, or parentheses only.

## 7. Generated Image Art Direction

This section governs the images an AI digest generates: the per-chapter teaching cards and the summary image. It is the executable contract a designing agent (Codex or any image-capable agent) follows when it creates those images.

**North star: inspired visual learning.** The standard is the clean, spacious, typographic craft of high-end product pages, but the goal is teaching, not template compliance. Each image should make a digest idea easier to grasp, more memorable, and more pleasurable to look at. Premium visuals may use full color, cinematic atmosphere, rich focal imagery, diagrams, or card strips when those choices help the viewer feel curiosity, recognition, and inspired understanding.

This is a different surface from the app chrome. The dark operator UI in Sections 2 through 6 governs buttons, cards, and nav inside the app. Generated digest images follow the premium direction below and may be light, dark, full-color, photographic, diagrammatic, or mixed when the concept calls for it. The bar is not a theme; the bar is quality and learning impact.

### Where these images appear

- **Chapter teaching card:** one per digest chapter, six maximum, saved as `generated/chapter-NN-<slug>.webp` and referenced from the chapter as `"images": ["generated/chapter-NN-<slug>.webp"]`.
- **Summary image:** the first chapter image doubles as the project's `summary_image`, shown on dashboard cards at roughly 320px wide and as the share and social preview. It must read as a thumbnail, not only at full size.

### Format

- 16:9, at least 1280x720 (1600x900 preferred), WebP, roughly 50 to 120 KB. One image carries one idea.
- Legible at 320px wide: the eyebrow, headline, and one key element must read at thumbnail scale.

### Pick a visual system, then commit

Choose one visual system for the whole digest and hold its logic across all images. This is not a hard gate to one layout, one accent, or one background color. A coherent set can mix light and dark moments when the concept calls for it, as long as type, pacing, composition, and palette feel authored rather than accidental.

- **Light** (default for explanatory or diagrammatic content): canvas pure white (`#ffffff`) or light grey (`#f5f5f7`). Headline near-black (`#1d1d1f`), body secondary grey (`#6e6e73`).
- **Dark** (for dramatic, data-forward, or photographic content): canvas true black (`#000000`) to charcoal (`#101012`). Headline white (`#f5f5f7`), body grey (`#a1a1a6`).
- **Full-color premium** (for inspired visual learning): use a concept-led palette with saturated focal color, gradients, atmosphere, data color, or illustrative color when it increases comprehension, emotion, and recall. Full color must be composed, not random category coloring.

### Card craft

The reusable card recipes live in the infographic skills: `simple-infographic` for quiet text-led card strips, `premium-infographic` for adaptive full-color visual-learning infographics, and `agnostic-infographic` for shared neutral rules. Use the style the operator chooses. Premium generated assets should use the strongest available image path for the bitmap visual, with local post-processing allowed for type, cropping, WebP conversion, and placement. This section sets a quality bar, not a rigid house template.

For generated digest images, "one card" means one cohesive teaching image. That image may be a single hero diagram, a large data figure, or a polished horizontal strip of subcards when the chapter is best explained as one workflow or capability set. Do not force a useful card-strip idea into one lone icon.

The focal composition is chosen per chapter: full-color editorial card strip, one large confident data figure, cinematic metaphor, map/status scene, process flow, comparison tableau, abstract teaching image, or another concept-specific form. Reverse-engineer the evidence first, then choose the form that teaches the concept best.

### Color and visual-reward discipline

- **Teaching first.** Color should clarify relationships, hierarchy, sequence, contrast, status, or emotional stakes.
- **Full color is allowed and encouraged in premium.** Use it to make the image pleasing to the mind and eye, giving the viewer a small reward for understanding the concept.
- **Avoid arbitrary color.** A different bright hue per box still reads as slop when the hues do not teach anything. If color varies, the variation must encode meaning, mood, focal emphasis, or scene identity.
- **Operator Blue remains the product accent.** It is available for system diagrams and labels, but premium images are not limited to blue-only line art.

### Typography

- **Inter** for headlines and body (the product's UI font), or the nearest clean grotesk the generator supports (Helvetica Neue, the system UI sans). Never a default serif, never Arial as a look.
- Hierarchy from **size and weight**, never from color. Headlines are tight and confident; body is calm and legible.

### Named rules

- **The Craft Rule.** Alignment, optical balance, and generous whitespace are not optional polish; they are the design. A cramped or misaligned card fails even if every element is "correct."
- **The One-Idea Rule.** One generated image states one idea. A card strip is acceptable when every subcard supports that same idea; if the image needs a second headline-level idea, it needs a second chapter.
- **The Inspired-Learning Rule.** A premium image should make the idea feel worth understanding. Beauty, color, novelty, and visual reward are valid teaching tools when they preserve the facts.
- **The Adaptive-Structure Rule.** Premium images are not hard-gated to a single card-strip grammar, theme, or palette. Choose the structure that fits the digest concept.
- **The No-Truncation Rule.** Every label is fully written. Ellipsis truncation ("3. Craft...") and text clipped by the edge are defects. Shorten the wording; never clip glyphs.
- **The No-Collision Rule.** Lines, arrows, and connectors never cross text. Leave a clear gap.
- **The No-Redundant-Controls Rule.** Static generated digest images do not show fake plus buttons, expand links, carousel arrows, pagination dots, or other nonfunctional controls. The image is the artifact; the reader UI already supplies navigation and interaction.
- **The Coherent-Set Rule.** The set shares design authorship: type quality, composition discipline, image sharpness, and visual-learning intent. It may adapt color and structure per chapter when the concepts need different teaching forms.

### Banned (these read as AI slop, in either theme)

- glowing robots, androids, mascots, brains, or "AI" faces
- neon glow, bloom, lens flare, holographic or HUD treatments, particle fields, starfields
- purple-to-magenta or cyberpunk gradients; gradient text
- faux-3D renders or glassy chrome used as decoration
- arbitrary rainbow category palettes where color has no teaching role
- drop shadows used as decoration (a subtle, realistic shadow under a real product photo is fine; a soft shadow under every flat card is not)
- grids of identical icon + heading + text tiles that read as wallpaper rather than one composed teaching card
- generic default fonts presented as the type style (Arial, DejaVu, Liberation)
- decorative grid lines, random colored bars, clip-art arrows, or filler ornament
- fake plus buttons, expand affordances, carousel arrows, pagination dots, or other redundant static controls
- truncated or edge-clipped text, and any line crossing a label

### Building the generation prompt

Start from the base image-generation prompt in the **agnostic-infographic** or **premium-infographic** skill, then bind these project values into it before calling the image model:

- **Visual-learning goal:** what the viewer should understand faster, remember longer, and feel inspired by.
- **Composition:** the form that fits the chapter: card strip, hero diagram, data scene, map/status surface, cinematic metaphor, process flow, or comparison tableau.
- **Palette:** concept-led full color when useful; restrained when the concept calls for calm. Color must teach or reward, not decorate randomly.
- **Type:** Inter (or the nearest clean grotesk the generator supports).
- **Per chapter:** the `Show:` line carries the chapter's one idea plus its concrete specifics (numbers, benchmark names, proper nouns, named examples).
- **Constraints:** source-copying, unreadable text, fake controls, and rights violations remain hard stops. Layout and palette are adaptive.

### Acceptance checklist (run this before referencing any image)

This is `detect`, applied to images. Use it as a design review, not a template lock. Source-copying, illegible text, fake controls, and rights issues are hard stops; layout, palette, and imagery should adapt until the image teaches well.

- [ ] Reads like premium visual learning: one idea, generous whitespace, precise alignment, and a memorable mental model.
- [ ] Structure adapts to the chapter concept rather than forcing a generic template.
- [ ] Color is concept-led and pleasing; full color is welcome when it teaches, inspires, or improves recall.
- [ ] Inter-style grotesk; hierarchy from size and weight, not color; no gradient text.
- [ ] Eyebrow + headline structure present; headline tight and confident; at most two headline lines.
- [ ] Every label fully written; nothing truncated or clipped by the edge; no line crosses text.
- [ ] One idea per image; if it uses subcards, every subcard supports the same chapter idea and the chapter's concrete specifics are present and correct.
- [ ] No redundant static controls: no plus buttons, expand links, carousel arrows, or pagination dots.
- [ ] No robot, mascot, copied face, hologram, faux-3D decoration, or grid of identical tiles.
- [ ] No decorative drop shadows (subtle shadow under a real product photo only).
- [ ] Readable at 320px thumbnail width.

### How an agent uses this

The design context lives in `docs/impeccable/` (this file and PRODUCT.md). Point the impeccable loader at it before generating images:

```
IMPECCABLE_CONTEXT_DIR=docs/impeccable
```

The AI digest task prompt (`tools/create_ai_digest_version.py`) and the help-demo skill instruct the digest agent to load this context, reverse-engineer source evidence, build images with the infographic skills, and satisfy the checklist above before referencing any image. This section sets the learning bar; the skills provide the craft. If the agent cannot meet the bar for a chapter, it ships fewer images and records the gap in `operator_image_note`; it never ships an off-brand image to fill a slot.
