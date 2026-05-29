---
name: agnostic-infographic
description: Create brand-neutral premium infographic systems from raw content, screenshots, product/service facts, or design references. Use when Antigravity needs to design, build, or prompt image models for horizontal card carousels, feature explainers, purchasing benefit cards, product discovery modules, comparison sections, or clean editorial UI infographics without copying source brands, logos, protected product names, or proprietary wording.
---

# Agnostic Infographic

## Overview

Create clean, premium, brand-neutral infographic sections that explain products, services, features, buying reasons, or comparison choices through a horizontal set of large visual cards.

Use this skill to turn dense information into a scannable card system with restrained copy, generous whitespace, crisp hierarchy, and strong image-led storytelling.

When the task asks for one of the two house infographic styles, prefer the dedicated skills:

- `simple-infographic` for quiet text-led benefit cards with simple support visuals.
- `premium-infographic` for immersive image-led discovery cards with varied focal imagery.

For generated AI digest images, a "single idea" can be expressed as one cohesive card strip. Do not collapse every digest image into a lone icon or node diagram when the stronger teaching form is a polished row of subcards that together explain one workflow, benefit set, or decision path.

## Visual Recipe

Build from these reusable visual patterns:

- Page stage: soft light-gray background, full-width section, generous top and bottom padding, centered content rail.
- Section header: large bold headline above the card row; optional small text links aligned to the right on wide screens.
- Card row: horizontal carousel or scroll-snap strip with 5 to 7 visible cards on desktop and partial overflow at the edge.
- Card shape: tall rounded rectangles, white or very soft pastel surfaces, subtle or absent shadow, overflow hidden.
- Card rhythm: equal card heights, consistent gutters, top-aligned text, imagery anchored to the lower half or used as a full-bleed background.
- Typography: modern neutral sans-serif, heavy compact headlines, short supporting copy, high contrast, no decorative type.
- Interaction cue: use only in real interactive UI, never in static/generated infographic images.
- Carousel controls: use only when implementing an actual carousel UI, never as decoration inside an infographic image.
- Image treatment: product renders, lifestyle crops, simple line illustrations, maps/status graphics, or icon systems that fill the lower card area.
- Color: mostly neutral surfaces with selective saturated accents for icons, status graphics, buttons, or product highlights.

## Content Model

Treat every card as one idea:

```text
Eyebrow: 1 to 3 words naming the category.
Title: 4 to 10 words with a concrete user benefit.
Body: 1 to 2 short lines explaining the benefit.
Visual: one product, person, icon scene, abstract diagram, or comparison image.
Action: optional only for real interactive UI; omit from static/generated infographic images.
```

Prefer plain, transferable categories:

- Ways to buy
- Trade-in
- Education
- Delivery
- Setup
- Customization
- Support
- Health
- Fitness
- Safety
- Connectivity
- Personalization
- Guided shopping
- Compare models

Rewrite source-specific copy into neutral, reusable language. Keep the user's actual product names only when the user provides or owns them.

## Layout Patterns

### Benefit Carousel

Use for purchasing reasons, service perks, onboarding, support, or feature summaries.

- Cards are mostly white.
- Text sits in the top third.
- Product, packaging, portrait, or icon illustration sits in the bottom half.
- Keep body copy compact so the visual has room to breathe.

### Feature Discovery Carousel

Use for "get to know" sections, product capabilities, or lifestyle-driven education.

- Mix card backgrounds: dark data cards, photo cards, map/status cards, pale color cards, and product-detail cards.
- Let imagery occupy most of each card.
- Overlay text in the upper-left with enough contrast.
- Use one vivid visual metaphor per card.

### Comparison Explorer

Use for product families, plan tiers, or model selection.

- Place a wide white comparison panel below the card row or section heading.
- Show 2 to 4 item columns with product images at the top, swatches or small selectors below, concise specs, price/starting point, and primary action.
- Use a sticky or floating compare control only when it helps repeated scanning.

### Digest Teaching Card Strip

Use for generated AI digest images when one chapter teaches a workflow or capability with several supporting parts.

- Treat the whole image as one teaching card with one headline and one idea.
- Place 4 to 5 subcards in a single horizontal row beneath the headline.
- Each subcard should have a short eyebrow, compact title, one optional body line, and one simple Operator-Blue line visual.
- Use one tinted subcard at most to create rhythm. Do not tint every card.
- Do not include nonfunctional plus buttons, expand links, carousel arrows, pagination dots, or other static controls in generated digest images. They are redundant unless the chapter itself is explicitly teaching that control.
- The image should read at thumbnail size through the section headline and row shape. Individual subcard body text may be secondary.

## Workflow

1. Inventory the content.
   - List the user's categories, benefits, products, services, or features.
   - Collapse duplicates and keep one promise per card.
   - Decide whether the section is a benefit carousel, feature discovery carousel, comparison explorer, digest teaching card strip, or mixed page.

2. Write the card copy.
   - Use short category labels.
   - Make titles benefit-led and concrete.
   - Keep body copy under two lines when possible.
   - Avoid legal-looking footnote markers unless the user explicitly supplies required notes.

3. Assign visuals.
   - Use product renders for concrete offers.
   - Use lifestyle photos for human outcomes.
   - Use line illustrations for service, setup, support, or abstract processes.
   - Use diagrams, maps, metrics, or status graphics for data-heavy features.
   - Keep every visual tied to the card's single promise.

4. Build the responsive layout.
   - Desktop: wide horizontal row with consistent card heights and scroll overflow.
   - Tablet: 2 to 3 cards visible with snap points.
   - Mobile: one large card per view, 82vw to 90vw width, with accessible swipe and buttons.
   - Preserve equal heights and stable control positions across breakpoints.

5. Sanitize the result.
   - Remove source logos, source product names, source-specific slogans, proprietary icons, and copied legal copy unless the user owns or explicitly authorizes them.
   - Replace copied examples with neutral placeholders or the user's own brand vocabulary.
   - Keep the visual grammar, not the source identity.

## Output Templates

When producing a design brief, use:

```text
Section goal:
[What the infographic teaches or helps the user decide.]

Layout:
[Benefit carousel, feature discovery carousel, comparison explorer, or mixed page.]

Cards:
1. [Eyebrow] | [Title] | [Body] | [Visual direction]
2. [Eyebrow] | [Title] | [Body] | [Visual direction]

Interaction:
[Scroll behavior, expand buttons, controls, links. Use "none" for static/generated infographics.]

Responsive notes:
[Desktop/tablet/mobile behavior.]
```

When producing an image-generation prompt, use:

```text
Create a clean brand-neutral infographic teaching card on a soft light-gray background. Use a large bold headline above a horizontal row of polished rounded subcards. Each subcard has a small category label, a compact bold title, one optional supporting line, and a simple Operator-Blue line visual anchored in the lower half. Use mostly white cards with at most one soft sky-tinted card for rhythm. Omit fake plus buttons, expand links, carousel arrows, pagination dots, and other nonfunctional controls. Use modern neutral sans-serif typography, high contrast, generous whitespace, consistent gutters, sharp line art, and a polished premium product-page aesthetic. Do not include real logos, copied product names, source-site labels, or legal marks.
```

## Quality Bar

- The row should be scannable in under 5 seconds.
- Every subcard should communicate one distinct supporting part of the larger image idea.
- Text should never fight the visual; image crops must leave room for the copy.
- Static generated digest images should not include decorative controls; the teaching content should carry the composition.
- The design should feel quiet, premium, and useful rather than like an ad collage.
- The final output must remain brand-neutral unless the user supplies their own brand system.
