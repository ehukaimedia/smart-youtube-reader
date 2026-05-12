# Product

## Register

product

## Users

A technically capable operator who studies long-form YouTube content (trading, markets, AI, engineering) and turns it into mental models. They run the app locally, share archives over Tailscale, and feed the resulting structured artifacts to AI agents and chat tools for learning, recall, and synthesis. They are comfortable with CLIs, JSON, and dev servers. They are usually working at a desk, on a dark screen, with multiple tools open. They do not need hand-holding; they need their tools to stay out of the way.

The job to be done: capture a video, review the AI-digested archive, hand it to an AI to learn from. Repeat at scale across a growing library. Group several archives into a combined digest when synthesis across videos is the goal.

## Product Purpose

Smart YouTube Reader turns any YouTube URL into a structured, AI-readable archive — transcript with timestamps, de-duplicated frames, semantic chapters, optional AI-generated digest versions, and group digests across multiple sources. The app exists so the operator does not have to re-watch hours of video to find the durable lessons inside it; the AI does that work, and the resulting archive is then re-usable by other AI tools.

Success looks like: opening a project, glancing at its structure, copying a learning prompt or sharing a link, and having an AI agent immediately produce useful synthesis. Failure looks like: getting lost in the UI, repeating work because actions are scattered, or producing artifacts the AI cannot easily consume.

## Brand Personality

Work-focused. Restrained. Calm. Dense without clutter. Dark by default because the operator works at night and in dim rooms. Closer in spirit to a terminal, a dataroom, or a developer tool than to a content-consumption product.

Three words: deliberate, quiet, durable.

Voice: direct sentences, no marketing hype, no exclamation marks. Labels are nouns and verbs ("Open Project", "Copy Learning Prompt"), never adjectives ("Awesome!", "Magical!"). Status messages are factual ("2 selected for group digest"), never celebratory.

## Anti-references

This product should not look or feel like:

- **SaaS marketing landing pages.** No hero gradients, no animated illustrations, no "Trusted by" logo strips, no scroll-driven feature reveals.
- **The hero-metric template.** Big number, small label, gradient accent — this SaaS-dashboard cliché does not belong on a working library.
- **Glassmorphism by default.** Heavy backdrop blurs and translucent cards as a stylistic reflex. The current `.glass-card` is legacy and should not be extended.
- **Gradient text.** The current `.title-gradient` (background-clip on a white-to-grey gradient) is exactly the anti-pattern to retire. Hierarchy comes from weight and size, never from a fade.
- **Card grids of identical icon+heading+text tiles** that flatten content variety into wallpaper.
- **Modal-first interaction.** Confirms and toasts in place; modals only when the action is genuinely interruptive.
- **Notion, Linear, or Vercel pastiche.** These are good tools but this product is its own register; do not converge on their visual language.

## Design Principles

1. **Show the workflow, not the chrome.** Every surface should make the next step obvious. Group selection, reader actions, slicer steps — the path through the work is the first thing the eye should find.
2. **One primary action per surface; secondary actions in overflow.** Stop offering five equally-weighted buttons. The hero verb is visible; the rest sit behind a `⋯`. The capability is preserved; the noise is not.
3. **Conditional UI for stateful chrome.** If a bar represents a selection, do not render it when nothing is selected. Empty controls teach the user to ignore them.
4. **Reading-comfortable typography.** Article columns cap at 72ch. Full-width body text is treated as a defect.
5. **Real artifact content over decorative placeholders.** Stats, titles, chapter names should reflect what the operator actually has. Lorem ipsum and "Project 1 / Project 2" are not acceptable in any preview, mock, or empty state.
6. **Preserve handlers, refactor presentation.** Existing copy/download/share/group flows work; UI work should reorganize them, not rewrite them. Behavior is stable; the surface gets calmer.

## Accessibility & Inclusion

- WCAG AA contrast minimum for text and interactive elements against the dark surface. The current near-black `--background: #050505` and white foreground pass; tinted neutrals on cards must be checked when changed.
- Every icon-only button carries an `aria-label` or `title`. Overflow `⋯` menus are keyboard-reachable and announce as menus.
- Focus rings are visible on dark surfaces — never `outline: none` without a replacement.
- Hit targets meet 36×36px minimum; the existing `× delete` glyph at 1.2rem with no padding is below this and is treated as a bug.
- Reduced motion: spinners and blinks honor `prefers-reduced-motion`. State transitions remain (the operator needs to see what changed) but ambient motion stops.
- Color is not the sole carrier of meaning. Status badges pair color with text ("complete", "processing", "failed"); selection state pairs the accent fill with a label change ("Add to Group" → "Selected").
