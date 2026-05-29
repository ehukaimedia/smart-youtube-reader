---
name: reverse-engineer-images
description: Reverse-engineer original video slice frames, screenshots, diagrams, slides, and other reference images into source-agnostic image-generation briefs. Use when Antigravity is creating AI digest images from Smart YouTube Reader archives, inspecting chapter image entries such as slice frame paths or source frame paths, deriving visual evidence from source pixels, and producing novel generated teaching images under generated WebP paths without copying, cropping, tracing, branding, or reusing the original frames.
---

# Reverse Engineer Images

## Overview

Turn source images into transferable visual evidence for novel AI digest teaching images.

For Smart YouTube Reader, this skill is not about recreating source frames. It is about inspecting original video slices, extracting the lesson-bearing visual structure, and translating that evidence into an agnostic prompt brief for a new generated image.

## Core Rule

Source frames are evidence only. Output images for generated AI digests must be new teaching visuals saved under `generated/*.webp`.

Do not copy, crop, trace, screenshot, restyle, or directly reproduce original frames, thumbnails, source UIs, logos, people, proprietary layouts, or brand trade dress. Preserve the lesson and concrete facts; transform the visual expression.

## Workflow

1. Inspect the source pixels.
   - Read the archive JSON and chapter text.
   - For each relevant source chapter, open every available image in `images`, including paths like `frames/<file>` and `slices/<slice_id>/frames/<file>`.
   - Use transcript and `timestamp_start` / `timestamp_end` to understand why the frame matters.
   - Prefer frames that show slides, charts, diagrams, tables, UI states, before/after comparisons, product/workflow evidence, or visual claims not present in transcript text.

2. Extract evidence, not style for copying.
   - Capture factual visual content: names, numbers, labels, axes, relationships, steps, comparisons, direction of claims, visible states, and concrete examples.
   - Capture visual structure: hierarchy, grouping, sequence, contrast, layout relationship, annotation pattern, and what the viewer is meant to notice.
   - Ignore non-essential source identity: presenter face, channel styling, decorative backgrounds, logos, website chrome, camera angle, exact colors, and proprietary UI details.

3. Convert source-specific visuals into agnostic teaching forms.
   - Slide or dense text -> one calm headline plus a small supporting diagram.
   - Chart or table -> simplified data figure, comparison, or trend card with only the necessary labels.
   - UI screenshot -> abstract interface/workflow diagram with generic panels and labels.
   - Product demo -> generic object, system, or process illustration focused on the lesson.
   - Presenter shot -> omit the person and visualize the concept they are explaining.
   - Brand-heavy frame -> replace brand marks with neutral category labels or the user's authorized brand vocabulary.
   - Multi-step explanation -> a concise flow or one cohesive card strip, not a wall of unrelated boxes.

4. Build a digest image brief.
   - State the digest chapter concept and source indices.
   - List the visual evidence to preserve.
   - Name the transformed visual metaphor.
   - Specify the output as a novel generated teaching image, not a recreated source frame.
   - If this repo's `agnostic-infographic` skill applies, use its card grammar for carousel/card-system visuals.
   - If this repo's Impeccable design context applies, follow `docs/impeccable/DESIGN.md` "Generated Image Art Direction".

5. Generate and validate.
   - Keep one idea per image.
   - Use a consistent theme, type scale, and accent across the digest image set.
   - Validate against both source evidence and output novelty: the image should preserve the lesson while clearly not being a copied frame.

## Evidence Notes Format

Use this compact note shape before writing an image prompt:

```text
Source chapters:
- [index] [concept] ([timestamp_start]-[timestamp_end])

Source images inspected:
- [path]: [what is visible and why it matters]

Visual evidence to preserve:
- [fact, relationship, number, label, comparison, or state]

Source identity to remove:
- [logos, faces, exact UI, source colors, proprietary layout, channel styling]

Transformed teaching visual:
- [diagram, data figure, line-art card, abstract UI flow, comparison card, checklist, etc.]
```

## Digest Image Prompt Pattern

Use this when creating generated AI digest images:

```text
Create a novel source-agnostic AI digest teaching image, 16:9.

Digest concept: [chapter concept].
Source evidence: [specific facts, numbers, relationships, or visual claims learned from inspected frames].

Show: [one transformed teaching idea, not the source frame]. Use [diagram/data figure/line-art/card system/workflow/comparison] to explain [lesson].

Layout: [theme and composition]. Use a small eyebrow label, one bold readable headline, optional one-line body, and one focal visual element. The focal element may be a polished row of subcards when the chapter teaches one workflow through several supporting parts. Keep generous margins, precise alignment, and clear hierarchy.

Style: clean premium product-marketing infographic, restrained color, modern neutral sans-serif, no clutter.

Do not include: copied source frames, screenshots, logos, presenter faces, source-specific UI chrome, protected product names unless authorized, watermarks, dense text walls, decorative effects, fake plus buttons, carousel arrows, pagination controls, or any visual that looks like a crop or trace of the original video.
```

For concise requests, return only the final prompt. For AI digest work, include evidence notes plus the final prompt unless the user asks otherwise.

## Output Shape

```text
Reverse-engineered evidence:
[Brief notes from inspected frames.]

Generated image prompt:
[Paste-ready prompt for a novel digest teaching image.]

Avoid:
- [source-copying risk]
- [likely generation failure]

Validation:
- Evidence preserved: [yes/no and what]
- Source identity removed: [yes/no and what]
- Novel output path: generated/[filename].webp
```

## Validation Checklist

- Every referenced source image was actually inspected.
- The prompt preserves the chapter's durable lesson, not filler decoration.
- Facts and claim direction from the source are not inverted or softened.
- The output image is novel and uses `generated/*.webp`, never a source frame path.
- Logos, exact UI, presenter faces, copied layouts, and protected trade dress are removed unless the user owns or explicitly authorizes them.
- The image can stand alone as a teaching card at thumbnail size.
- The prompt has one clear focal idea and does not ask for a collage of every source detail. If it uses subcards, they all support the same chapter idea and avoid nonfunctional controls.

## Safety And Rights

- Treat video slices, screenshots, UI frames, ads, thumbnails, and slides as reference evidence, not reusable art.
- Prefer transformed diagrams, abstracted UI, neutral product/category labels, and original compositions.
- Preserve proper nouns only when they are necessary factual content for the lesson or supplied by the user as authorized brand vocabulary.
- Do not promise pixel-identical reproduction. The goal is faithful teaching value, not visual duplication.
