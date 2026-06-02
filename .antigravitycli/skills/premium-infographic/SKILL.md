---
name: premium-infographic
description: Create brand-neutral premium image-led infographic systems from product, service, feature, workflow, or digest content. Use when Antigravity needs immersive visual-learning cards, editorial feature explainers, cinematic product capability strips, or generated high-definition infographics with rich full-color focal imagery that teaches, inspires, and avoids copied source branding or navigation controls.
---

# Premium Infographic

## Overview

Create an image-led infographic system where each image feels like a polished editorial teaching artifact. This style is best for capability discovery, feature education, lifestyle outcomes, data moments, product-like storytelling, and digest chapters that benefit from a strong visual metaphor.

Premium is not a rigid card-strip template. The structure adapts to the concept: a cinematic card row, a single hero diagram, a layered data scene, a map-like teaching surface, a process flow, or a rich abstract metaphor are all valid when they explain the digest better. The end goal is inspired visual learning: the image should be pleasing to the mind and the eye, create curiosity, and make the human feel rewarded for understanding the idea.

Use reference images to reverse-engineer composition, hierarchy, and pacing only. The output must be novel and brand-neutral: no copied logos, product names, slogans, proprietary UI, people from the source, protected device shapes, or source trade dress unless the user owns and explicitly requests them.

## Style Signature

- Clean white or very light page stage with a centered section headline.
- Wide horizontal row of tall rounded cards, usually 5 to 8 visible cards.
- Cards are image-dominant: visual fills most of the card or becomes the background.
- Text overlays in the upper-left with strong contrast and short line lengths.
- Surfaces vary deliberately: dark data card, photographic card, map/status card, pale tint card, object-detail card, abstract illustration card.
- Each card has one vivid focal metaphor and one emotional or functional promise.
- Typography is modern neutral sans-serif, bold and compact.
- Color is full and concept-led. Use a rich palette when it teaches and inspires, but compose it deliberately; avoid arbitrary rainbow category tiles.

## Inspired Visual Learning

Premium infographics should increase understanding by increasing desire to look. They should do more than summarize text: they should create a mental model.

- Teach first: every visual decision should clarify a relationship, sequence, contrast, mechanism, consequence, or memorable example from the digest.
- Reward the eye: use full color, depth, texture, atmosphere, and cinematic composition when they make the idea easier and more pleasurable to grasp.
- Customize to the concept: reverse-engineer the digest evidence, then choose the visual language that fits that concept rather than forcing a house layout.
- Balance emotion and precision: visual reward comes from beauty, novelty, and recognition, but the factual lesson must remain correct.
- Keep the output brand-neutral and rights-safe: full color never means copied trade dress, logos, source screenshots, or identifiable source people.

## Static Image Rule

For generated/static infographics, do not include nonfunctional plus buttons, expand links, carousel arrows, pagination dots, or navigation controls. A premium card strip should feel complete without fake UI chrome. Only show controls when building a real interactive UI and the controls will work.

## Generation Rule

Premium generated infographic images should use Gemini image generation for the bitmap visual, not local vector-only placeholders. Use the available image-generation path and keep the original generated PNG in the harness's generated-images location when one exists. Local post-processing is allowed for exact text overlay, cropping, WebP conversion, compression, and placement in the repo, but the focal imagery must come from the image model.

If the explicit CLI/API route is requested, use the configured Gemini image-generation route. If the CLI cannot run because credentials are missing, use the built-in image generation path available in Antigravity and clearly report that path. Do not silently substitute a hand-drawn Pillow/SVG/canvas image for a premium generated asset.

This generation rule is a production-path preference, not a creative hard gate. Do not reject a premium concept because it is not a carousel, not restrained enough, not blue-only, or not a prewritten template. Judge premium images by teaching impact, novelty, visual pleasure, evidence fidelity, rights safety, and polish.

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

- Data or health-like insight -> dark metric card with one glowing-but-controlled focal value or shape.
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
   - Keep the set coherent through intentional palette, type, composition, and recurring visual logic.
   - Let color adapt to the concept: energetic learning may need full color; calm explanation may need quieter color.

4. Produce the output.
   - For a web UI, build the row as real cards with accessible content.
   - For a generated image, make one high-definition strip with no fake navigation.

5. Validate.
   - Every card has a distinct focal visual.
   - Text has safe contrast and does not sit over noisy detail.
   - No copied brand, protected UI, or source person.
   - No navigation controls in static output.
   - The result feels sharp, cinematic, intentional, and mentally rewarding.
   - The image teaches something a reader can remember without rereading the paragraph.

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
Create a brand-neutral premium visual-learning infographic, 16:9. Reverse-engineer the digest concept and choose the composition that teaches it best: cinematic card strip, single hero diagram, layered data scene, map/status surface, process flow, or abstract metaphor. Use full color intentionally to make the idea pleasing, memorable, and inspiring while preserving factual clarity. Include a compact headline, short labels where useful, strong contrast, safe text zones, high-definition detail, and modern sans-serif typography. Make the visual concept custom to the digest rather than a generic template. Do not include logos, copied product names, source-site wording, identifiable source people, fake plus buttons, expand links, carousel arrows, pagination dots, navigation controls, gradient text that reduces legibility, mascots, or copied source trade dress.
```

## Quality Bar

- Feels like a high-end editorial product page, not a grid of utility tiles.
- Each card has a memorable visual concept.
- The palette is full-color and concept-led without becoming arbitrary, noisy, or collage-like.
- Text remains crisp, short, and readable over the imagery.
- The set is sharp, high-definition, brand-neutral, and complete without UI controls.
- The image induces curiosity and inspired understanding: the viewer should feel the concept, not just read it.
