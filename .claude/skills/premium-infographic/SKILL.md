---
name: premium-infographic
description: Use when you need an immersive, image-led infographic card strip from product, feature, capability, workflow, or digest content — cinematic discovery cards, editorial feature explainers, or a premium high-definition Smart YouTube Reader digest chapter with rich focal imagery, strong type, and no copied source branding or navigation controls.
---

# Premium Infographic

## Overview

Create an image-led infographic strip where each card feels like a polished editorial feature card. This style is best for capability discovery, feature education, lifestyle outcomes, data moments, product-like storytelling, and digest chapters that benefit from a strong visual metaphor.

Use reference images to reverse-engineer composition, hierarchy, and pacing only. The output must be novel and brand-neutral: no copied logos, product names, slogans, proprietary UI, people from the source, protected device shapes, or source trade dress unless the user owns and explicitly requests them.

## Style Signature

- Clean white or very light page stage with a centered section headline.
- Wide horizontal row of tall rounded cards, usually 5 to 8 visible cards.
- Cards are image-dominant: visual fills most of the card or becomes the background.
- Text overlays in the upper-left with strong contrast and short line lengths.
- Surfaces vary deliberately: dark data card, photographic card, map/status card, pale tint card, object-detail card, abstract illustration card.
- Each card has one vivid focal metaphor and one emotional or functional promise.
- Typography is modern neutral sans-serif, bold and compact.
- Color is disciplined per card; the set may have varied scenes, but avoid rainbow category tiles.

## Static Image Rule

For generated/static infographics, do not include nonfunctional plus buttons, expand links, carousel arrows, pagination dots, or navigation controls. A premium card strip should feel complete without fake UI chrome. Only show controls when building a real interactive UI and the controls will work.

## Generation Rule

A premium infographic is a **complete, high-craft editorial composition** — never a thin placeholder, a lone icon on white, or a half-finished template. Whatever path produces it, the focal imagery and layered surfaces must be fully realized.

Pick the path the harness actually supports:

- **Harness with a native image model:** generate the focal bitmap with the native image tool (e.g. GPT 5.5 image generation as specified by `docs/impeccable/DESIGN.md`). Local post-processing is allowed for exact text overlay, cropping, WebP conversion, compression, and repo placement, but the focal imagery comes from the image model.
- **Current Claude Code (no native image model):** author the entire card as a complete HTML/CSS/SVG editorial composition — layered flat surfaces, real depth, a confident focal metaphor, disciplined per-card color, and crisp type — then render it to raster at the exact output size (for Smart YouTube Reader digests: 1280x720) with headless Chrome (Playwright `channel="chrome"`, or the chrome-devtools MCP), and convert to WebP with `cwebp -q 82`. This fully realized render **is** the genuine designed artifact; browser-rendered type stays sharp and never truncates.

Do not ask the user to install image APIs or external tooling just to do this. If no image path and no rendering path is available, state in one line that the premium image step is skipped because the harness has neither, then proceed.

**Anti-slop bar (non-negotiable):** Do not ship a thin, templated, vector-stub, or unfinished card to fill a slot. A complete editorial HTML/CSS/SVG render that meets the quality bar below is a premium asset; an icon-on-white SVG stub is not. If a card cannot meet the editorial bar, cut it and note the gap rather than shipping an off-brand image.

## Content Model

Each card is a mini editorial poster:

```text
Eyebrow: 1 to 3 words naming the theme.
Title: 3 to 8 words with a memorable promise.
Body: optional; omit unless it adds clarity.
Visual: one dominant photo-like scene, diagram, data moment, map, product-neutral object, or abstract illustration.
Contrast plan: light text on dark/image cards, dark text on pale cards.
```

Prefer transferable themes such as:

- Health
- Fitness
- Safety
- Creativity
- Productivity
- Learning
- Collaboration
- Connectivity
- Personalization
- Entertainment
- Research
- Automation
- Sharing

## Layout Rules

- Let visuals take 65 to 85 percent of each card.
- Keep text in a protected upper-left zone; never let image details compete with the headline.
- Use large crops and confident focal shapes rather than many small icons.
- Vary card visual type across the row, but keep card geometry, radius, spacing, and type scale consistent.
- Use dark cards, tinted cards, and image cards purposefully; avoid making every card the same template.
- For generated 16:9 output, make the headline and first 3 to 5 cards readable at 320px wide.

## Visual Directions

Choose the strongest metaphor for the content:

- Data or health-like insight -> dark metric card with one controlled focal value or shape.
- Movement or momentum -> cropped action/lifestyle scene, no identifiable source person.
- Safety or location -> simplified map/status graphic with one central signal.
- Creative capability -> abstract illustration with texture and a single focal gesture.
- Communication -> neutral screen or call/status object, no real UI branding.
- Personalization -> object arrangement, swatches, or modular parts.
- Research/synthesis -> layered source cards merging into a clear outcome.

## Workflow

1. Pick the premium-worthy ideas.
   - Use this style only when visual richness helps the lesson.
   - Collapse utility details into fewer, stronger cards.

2. Write poster-like copy.
   - Short eyebrow, bold title, optional body.
   - Replace source-specific claims with neutral user outcomes.

3. Build visual variety.
   - Assign a distinct visual type to each card.
   - Keep the set coherent through geometry, type, and restrained color.

4. Produce the output.
   - For a web UI, build the row as real cards with accessible content.
   - For a generated image, make one high-definition strip with no fake navigation, using the path in Generation Rule.

5. Validate.
   - Every card has a distinct focal visual.
   - Text has safe contrast and does not sit over noisy detail.
   - No copied brand, protected UI, or source person.
   - No navigation controls in static output.
   - The result feels sharp, cinematic, and intentional.

## Design Brief Template

```text
Style: premium-infographic
Goal: [what the strip helps the viewer understand]
Headline: [large section headline]
Cards:
1. [Eyebrow] | [Title] | [Optional body] | [Dominant visual metaphor] | [Contrast plan]
2. ...
Static controls: none
Brand handling: remove source identity; keep only user-authorized names
```

## Image Prompt Template

```text
Create a brand-neutral premium image-led infographic strip, 16:9, on a clean light page stage. Use one large compact headline above a single row of tall rounded editorial cards. Each card has a short upper-left eyebrow and bold title, with optional minimal body copy. Make the visuals dominant and varied across the row: dark metric card, cinematic crop, map/status graphic, pale object-detail card, abstract illustration, or neutral screen scene as appropriate. Keep consistent card geometry, spacing, radius, and modern sans-serif typography. Ensure text has strong contrast and safe clear space. Do not include logos, copied product names, source-site wording, identifiable source people, fake plus buttons, expand links, carousel arrows, pagination dots, navigation controls, gradient text, neon effects, mascots, or decorative shadows.
```

## Quality Bar

- Feels like a high-end editorial product page, not a grid of utility tiles.
- Each card has a memorable visual concept.
- The row has variety without becoming a rainbow or collage.
- Text remains crisp, short, and readable over the imagery.
- The set is sharp, high-definition, brand-neutral, and complete without UI controls.
