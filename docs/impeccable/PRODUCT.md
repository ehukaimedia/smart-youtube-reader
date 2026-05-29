# Product

## Register

product

## Users

A technically capable operator who studies long-form YouTube content (trading, markets, AI, engineering) and turns it into mental models. They run the app locally, share archives over Tailscale, and feed the resulting structured artifacts to AI agents and chat tools for learning, recall, and synthesis. They are comfortable with CLIs, JSON, and dev servers. They are usually working at a desk, on a dark screen, with multiple tools open. They do not need hand-holding; they need their tools to stay out of the way.

The job to be done: capture a video, review the AI-digested archive, hand it to an AI to learn from. Repeat at scale across a growing library. Group several archives into a combined digest when synthesis across videos is the goal.

## Product Purpose

Smart YouTube Reader turns any YouTube URL into a structured, AI-readable archive — transcript with timestamps, de-duplicated frames, semantic chapters, optional AI-generated digest versions, and group digests across multiple sources. The app exists so the operator does not have to re-watch hours of video to find the durable lessons inside it; the AI does that work, and the resulting archive is then re-usable by other AI tools.

Success looks like: opening a project, glancing at its structure, copying a learning prompt or sharing a link, and having an AI agent immediately produce useful synthesis. Failure looks like: getting lost in the UI, repeating work because actions are scattered, or producing artifacts the AI cannot easily consume.

AI digests can also carry generated teaching images: one card per chapter, six at most, plus a summary image that becomes the project thumbnail. These images are drawn by an agent, not a person, so they are the surface most likely to drift into generic AI output. Treat them as first-class visual-learning artifacts: one durable idea, evidence-grounded structure, strong typography, generous whitespace, and concept-led color that helps the idea stick. Premium images may be full-color, cinematic, diagrammatic, data-rich, or card-based depending on the digest concept. They are always quality-designed and never a stock template. The executable rules live in the Generated Image Art Direction section of DESIGN.md.

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
- **Productivity-app pastiche.** This product is its own register; do not converge on the visual language of other well-known tools.
- **AI image slop, sci-fi register.** Generated digest images never show glowing robots, neon mascots, holographic HUDs, purple-to-magenta gradients, lens flare, or faux-3D renders. The reference is a premium product card, not launch key art.
- **AI image slop, generic-infographic register.** Banned just as firmly: arbitrary rainbow palettes, drop-shadowed clip-art tiles, generic system fonts presented as the type style, decorative grid lines, and truncated labels. Full color is welcome in premium digest images when it teaches and inspires; cheap is not. The bar is premium visual-learning craft, not a stock template.

## Design Principles

1. **Show the workflow, not the chrome.** Every surface should make the next step obvious. Group selection, reader actions, slicer steps — the path through the work is the first thing the eye should find.
2. **One primary action per surface; secondary actions in overflow.** Stop offering five equally-weighted buttons. The hero verb is visible; the rest sit behind a `⋯`. The capability is preserved; the noise is not.
3. **Conditional UI for stateful chrome.** If a bar represents a selection, do not render it when nothing is selected. Empty controls teach the user to ignore them.
4. **Reading-comfortable typography.** Article columns cap at 72ch. Full-width body text is treated as a defect.
5. **Real artifact content over decorative placeholders.** Stats, titles, chapter names should reflect what the operator actually has. Lorem ipsum and "Project 1 / Project 2" are not acceptable in any preview, mock, or empty state.
6. **Preserve handlers, refactor presentation.** Existing copy/download/share/group flows work; UI work should reorganize them, not rewrite them. Behavior is stable; the surface gets calmer.
7. **Generated images create inspired visual learning.** A digest's teaching images follow the premium art direction in DESIGN.md: one durable idea, evidence-grounded visual structure, strong typography, generous whitespace, and concept-led color. Premium visuals adapt to the digest rather than forcing a template; the goal is to make humans feel rewarded and inspired while understanding the lesson, with enough visual structure to help AI systems reason over the digest too. An agent that cannot meet the quality bar ships fewer images, never off-brand ones. The executable spec is the Generated Image Art Direction section of DESIGN.md.

## Accessibility & Inclusion

- WCAG AA contrast minimum for text and interactive elements against the dark surface. The current near-black `--background: #050505` and white foreground pass; tinted neutrals on cards must be checked when changed.
- Every icon-only button carries an `aria-label` or `title`. Overflow `⋯` menus are keyboard-reachable and announce as menus.
- Focus rings are visible on dark surfaces — never `outline: none` without a replacement.
- Hit targets meet 36×36px minimum; the existing `× delete` glyph at 1.2rem with no padding is below this and is treated as a bug.
- Reduced motion: spinners and blinks honor `prefers-reduced-motion`. State transitions remain (the operator needs to see what changed) but ambient motion stops.
- Color is not the sole carrier of meaning. Status badges pair color with text ("complete", "processing", "failed"); selection state pairs the accent fill with a label change ("Add to Group" → "Selected").
