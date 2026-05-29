---
name: simple-infographic
description: Create brand-neutral simple infographic card strips from product, service, workflow, or digest content. Use when Codex needs a quiet text-led benefit carousel, purchasing/service explainer, onboarding strip, or generated static infographic with white cards, restrained visuals, and no copied source branding or navigation controls.
---

# Simple Infographic

## Overview

Create a calm, brand-neutral infographic strip where the copy explains the idea and the visuals support it. This style is best for benefits, services, buying reasons, onboarding steps, support options, digest chapters, and workflow explanations that should feel clear rather than cinematic.

Use the source reference as visual grammar only. Do not copy source brands, logos, product names, slogans, legal marks, people, device trade dress, or proprietary layouts unless the user owns and explicitly requests them.

## Style Signature

- Soft light-gray page stage (`#f5f5f7`) with a centered content rail.
- One large compact headline above the row; optional short link only for real UI, not static image output.
- 5 to 8 tall rounded white cards with equal height and consistent gutters.
- Card text sits in the top third: small eyebrow, bold title, one short supporting line.
- One visual sits in the lower half: product-neutral object, package, abstract UI panel, icon scene, or simple line diagram.
- Mostly white cards; at most one very soft tint (`#e8f0fb`) for rhythm.
- Modern neutral sans-serif, high contrast, no decorative type.
- Flat surfaces with subtle borders; avoid decorative shadows.

## Static Image Rule

For generated/static infographics, do not include nonfunctional plus buttons, expand links, carousel arrows, pagination dots, or navigation controls. The image itself is the artifact. Only show controls when building an actual interactive UI and the controls will work.

## Content Model

Each card carries one practical promise:

```text
Eyebrow: 1 to 3 words naming the category.
Title: 4 to 9 words, concrete and benefit-led.
Body: 1 short sentence or two short lines.
Visual: one clean support visual anchored low in the card.
```

Use transferable categories such as:

- Ways to start
- Save time
- Setup
- Delivery
- Support
- Search
- Evidence
- Archive
- Sharing
- Customization
- Compare
- Safety

## Layout Rules

- Keep outer margins generous, about 8 to 12 percent of the canvas or viewport.
- Align card tops and baselines precisely.
- Keep card interiors airy; do not let body copy run into the visual.
- Prefer one row. For static 16:9 output, use 4 to 6 cards if the canvas is narrow or thumbnail readability matters.
- Use simple visual variety through icon/object choice, not many colors.
- Make the headline and row shape readable at 320px wide.

## Workflow

1. Inventory the content.
   - List the benefits, steps, services, or chapter subideas.
   - Collapse duplicates until each card has one job.

2. Rewrite into neutral copy.
   - Remove source-specific words unless they are the user's authorized terms.
   - Prefer short verbs and concrete outcomes.
   - Avoid footnote markers, legal copy, and copied promotional phrases.

3. Assign simple visuals.
   - Service/support -> line icon scene.
   - Workflow -> abstract UI panel or small process diagram.
   - Evidence/content -> folder, document, timestamp, frame, list, or search metaphor.
   - Delivery/sharing -> package, link, endpoint, or device-neutral screen.

4. Produce the output.
   - For a web UI, build a responsive horizontal scroll strip without decorative controls.
   - For a generated image, make one cohesive teaching image with no fake navigation.

5. Validate.
   - One idea per card.
   - No source branding or protected trade dress.
   - No navigation controls in static output.
   - Text is fully visible and not clipped.
   - Visuals are sharp, simple, and secondary to the explanation.

## Design Brief Template

```text
Style: simple-infographic
Goal: [what the strip explains]
Headline: [large section headline]
Cards:
1. [Eyebrow] | [Title] | [Body] | [Simple visual]
2. ...
Static controls: none
Brand handling: remove source identity; keep only user-authorized names
```

## Image Prompt Template

```text
Create a brand-neutral simple infographic teaching strip, 16:9, on a soft light-gray background. Use one large compact headline above a single row of tall rounded white cards. Each card has a small muted eyebrow, a bold short title, one brief supporting line, and one clean lower-half visual. Use a modern neutral sans-serif, near-black headlines, muted gray body text, flat white cards with subtle borders, and one blue accent for line art. Include at most one soft sky-tinted card. Do not include logos, copied product names, source-site wording, people, fake plus buttons, expand links, carousel arrows, pagination dots, navigation controls, gradients, glow, or decorative shadows.
```

## Quality Bar

- Feels quiet, useful, and premium.
- Reads from the headline first, then the card titles, then the visuals.
- Uses restraint: one accent, one row, one idea per card.
- Looks crisp at high resolution and still understandable as a thumbnail.
