---
name: agnostic-infographic
description: Create brand-neutral premium infographic systems from raw content, screenshots, product/service facts, or design references. Use when Codex needs to design, build, or prompt image models for horizontal card carousels, feature explainers, purchasing benefit cards, product discovery modules, comparison sections, or clean editorial UI infographics without copying source brands, logos, protected product names, or proprietary wording.
---

# Agnostic Infographic

## Overview

Create clean, premium, brand-neutral infographic sections that explain products, services, features, buying reasons, or comparison choices through a horizontal set of large visual cards.

Use this skill to turn dense information into a scannable card system with restrained copy, generous whitespace, crisp hierarchy, and strong image-led storytelling.

## Visual Recipe

Build from these reusable visual patterns:

- Page stage: soft light-gray background, full-width section, generous top and bottom padding, centered content rail.
- Section header: large bold headline above the card row; optional small text links aligned to the right on wide screens.
- Card row: horizontal carousel or scroll-snap strip with 5 to 7 visible cards on desktop and partial overflow at the edge.
- Card shape: tall rounded rectangles, white or very soft pastel surfaces, subtle or absent shadow, overflow hidden.
- Card rhythm: equal card heights, consistent gutters, top-aligned text, imagery anchored to the lower half or used as a full-bleed background.
- Typography: modern neutral sans-serif, heavy compact headlines, short supporting copy, high contrast, no decorative type.
- Interaction cue: small circular action button at the lower-right of each card, commonly a plus icon for expanding details.
- Carousel controls: compact circular previous/next buttons below the card row, centered or slightly right of center.
- Image treatment: product renders, lifestyle crops, simple line illustrations, maps/status graphics, or icon systems that fill the lower card area.
- Color: mostly neutral surfaces with selective saturated accents for icons, status graphics, buttons, or product highlights.

## Content Model

Treat every card as one idea:

```text
Eyebrow: 1 to 3 words naming the category.
Title: 4 to 10 words with a concrete user benefit.
Body: 1 to 2 short lines explaining the benefit.
Visual: one product, person, icon scene, abstract diagram, or comparison image.
Action: one unobtrusive expand/details control.
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

## Workflow

1. Inventory the content.
   - List the user's categories, benefits, products, services, or features.
   - Collapse duplicates and keep one promise per card.
   - Decide whether the section is a benefit carousel, feature discovery carousel, comparison explorer, or mixed page.

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
[Scroll behavior, expand buttons, controls, links.]

Responsive notes:
[Desktop/tablet/mobile behavior.]
```

When producing an image-generation prompt, use:

```text
Create a clean brand-neutral infographic section on a soft light-gray background. Use a large bold headline above a horizontal row of tall rounded cards. Each card has a small category label, a compact bold title, one short supporting line, and a strong visual anchored in the lower half. Mix white cards, soft pastel cards, product-render cards, lifestyle photo cards, and simple blue line-illustration cards. Add small circular plus buttons at the lower-right of each card and compact circular carousel arrows below the row. Use modern neutral sans-serif typography, high contrast, generous whitespace, consistent gutters, and a polished premium product-page aesthetic. Do not include real logos, copied product names, source-site labels, or legal marks.
```

## Quality Bar

- The row should be scannable in under 5 seconds.
- Every card should communicate one distinct reason, feature, or choice.
- Text should never fight the visual; image crops must leave room for the copy.
- Controls should feel functional, not decorative.
- The design should feel quiet, premium, and useful rather than like an ad collage.
- The final output must remain brand-neutral unless the user supplies their own brand system.
