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
    fontFamily: "Inter, -apple-system, BlinkMacSystemFont, Segoe UI, sans-serif"
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

**Display Font:** Inter (with `-apple-system, BlinkMacSystemFont, Segoe UI, sans-serif` fallback)
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
- **Don't** copy the visual language of Notion, Linear, or Vercel. This product is its own register.
- **Don't** use `#000` or `#fff`. Every neutral is tinted.
- **Don't** use em dashes in UI copy or labels. Commas, colons, semicolons, periods, or parentheses only.
