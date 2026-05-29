---
name: reverse-engineer-images
description: Reverse-engineer reference images into reusable image-generation prompts. Use when Codex needs to analyze an image, video frame, screenshot, ad, product mockup, poster, UI, or visual style and produce a prompt that can recreate it, generate close variants, or teach the user the visual language an image model responds to.
---

# Reverse Engineer Images

## Overview

Turn a visual reference into a practical generation prompt by reading the image first, then describing the exact canvas, layout, subjects, typography, color, lighting, texture, and rendering cues an image model needs.

This skill is based on the workflow demonstrated in "This One Prompt Unlocks ChatGPT Images 2.0": upload or inspect a reference, ask for a reverse-engineered prompt, run that prompt in a fresh generation context, compare the result to the original, then adjust the middle of the prompt for variants.

## Workflow

1. Inspect the visual source directly.
   - If the user provides an image, screenshot, local path, URL, video frame, archive, or digest with frame filenames, view the actual image evidence before writing the prompt.
   - Do not rely only on transcript text, alt text, filenames, or the user's summary when pixels are available.
   - If there are multiple frames, choose frames that show the final target, prompt text, diagrams, layout grids, before/after examples, or finished outputs.

2. Extract the image recipe.
   - Identify format: aspect ratio, orientation, crop, canvas shape, border radius, margins, and resolution feel.
   - Identify subject hierarchy: primary subject, secondary objects, foreground/background order, overlap, scale, and depth.
   - Identify composition: focal point, alignment, grid, negative space, perspective, camera angle, lens distance, and framing.
   - Identify text and typography: exact visible copy when appropriate, casing, line breaks, weight, font category, placement, hierarchy, and contrast.
   - Identify color system: dominant background, accent colors, saturation, gradients if present, material colors, and contrast relationships.
   - Identify lighting and rendering: studio light, shadows, reflections, glossy/matte finish, realism level, illustration style, grain, focus, and post-processing.
   - Identify domain cues: print ad, editorial photo, product render, app screenshot, packaging, infographic, social post, cinematic still, etc.
   - Identify exclusions: artifacts, clutter, wrong text, extra logos, distorted hands, unreadable type, watermarking, cropping mistakes, or off-brand details.

3. Write the generation prompt as a structured scene brief.
   - Start with the output type and goal.
   - State the canvas and composition early.
   - Describe subjects from largest and most important to smallest details.
   - Preserve exact text only when the user wants recreation and it is appropriate to reproduce.
   - Use clear visual language: "vertical 4:5 poster", "solid bright red background", "large bold white sans-serif headline", "glossy commercial food styling", "balanced negative space", "ultra-sharp focus".
   - Avoid vague praise like "beautiful" unless paired with visible specifics.

4. Add editable knobs.
   - Separate the stable anchors from optional changes.
   - When the user wants a variation, keep the image grammar fixed and change only the requested axis: product, palette, setting, copy, mood, camera angle, typography, or era.

5. Validate by comparison when generating is part of the task.
   - Generate from the prompt in a new context when possible.
   - Compare original and output side by side.
   - Check both macro similarity and small deltas: headline scale, subject size, object order, logo placement, price/detail blocks, negative space, crop, and background element position.
   - Revise the prompt from visible deltas: layout drift, wrong scale, text errors, missing objects, wrong lighting, wrong material, or clutter.

## Reverse-Engineering Request

When you need the model to analyze an attached/reference image before drafting the prompt, use this minimal request:

```text
Analyze this image and write a prompt that would get an image model to create it. Reverse engineer the prompt.
```

Then improve the returned prompt with the extraction checklist above. The first response is a draft, not the final artifact.

## Prompt Format

Use this output shape unless the user asks for something else:

```text
Reverse-engineered prompt:
[One cohesive prompt that can be pasted into an image model.]

Editable knobs:
- [Element]: [safe variations or user-controlled options]
- [Element]: [safe variations or user-controlled options]

Avoid:
- [Common failure mode]
- [Common failure mode]
```

For a concise prompt-only request, return only the prompt.

## Prompt Pattern

```text
Create [output type] in [style/domain].

Canvas and composition: [aspect ratio, orientation, crop, layout grid, focal point, negative space].

Primary subject: [main object/person/scene, scale, position, pose, material, detail level].

Supporting elements: [secondary objects, background shapes, icons, logos if appropriate, props, environmental context].

Typography/text: [exact text if needed, font category, size hierarchy, color, placement, line breaks].

Color and lighting: [palette, saturation, contrast, shadows, highlights, studio/natural/cinematic light].

Rendering: [photorealistic/illustrated/3D/vector/etc., texture, focus, lens/camera cues, print or digital finish].

Quality constraints: [clean composition, readable text, no clutter, no extra text, no distorted objects, no watermarks].
```

## Example Pattern From The Digest

The video's McDonald's-style ad example worked because the prompt named the visible structure, not because it was long for its own sake:

- A vertical poster with a bright red background.
- A large white headline in the upper left.
- Smaller yellow and white supporting copy under it.
- A glossy commercial burger, fries, and drink arranged in the bottom half.
- Cropped golden arches behind the food for depth.
- A small logo area, price block, bright studio lighting, saturated colors, and clean print-ad composition.

Use this level of specificity for any reference: describe what is visible, where it sits, how it is styled, and which details make the image feel like its category.

The updated side-by-side frames also show how to judge a reverse-engineered prompt:

- The generated ad can match the original's category, palette, headline, food subjects, logo cues, and offer block while still drifting in layout.
- Compare item-by-item instead of asking whether it "looks right": headline position, food stack scale, drink/fries order, golden arch crop, top logo placement, price block location, and empty red space.
- If the user wants closer recreation, tighten the geometry and relationships. If the user wants a variant, keep the stable style grammar and intentionally change only the requested element.

## Safety And Rights

- Do not promise pixel-identical reproduction; image models can drift.
- If the image contains a recognizable person, brand, logo, artwork, or copyrighted design, be clear when the prompt is for analysis, parody, internal exploration, or an owned/authorized asset.
- For public or commercial use, prefer transformed variants: preserve broad composition and production cues while changing protected names, exact copy, logos, distinctive characters, or proprietary trade dress unless the user has rights.
