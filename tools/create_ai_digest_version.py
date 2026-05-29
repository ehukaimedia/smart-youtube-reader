#!/usr/bin/env python3
"""Create an AI digest project from an external agent-authored draft."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from fastapi import HTTPException


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.digest import (  # noqa: E402
    DIGEST_AGENT_TASK,
    build_digest_user_prompt,
    materialize_digest_project,
    resolve_project,
    _extract_json_object,
    _read_json,
)


def main() -> int:
    try:
        return run()
    except HTTPException as exc:
        print(exc.detail, file=sys.stderr)
        return 1
    except (RuntimeError, OSError, ValueError, json.JSONDecodeError) as exc:
        print(str(exc), file=sys.stderr)
        return 1


def run() -> int:
    parser = argparse.ArgumentParser(
        description="Create a Smart YouTube Reader AI digest version from an agent-authored JSON draft."
    )
    parser.add_argument(
        "project",
        help="Source project folder path, data/jobs folder name, or job_id from manifest.json.",
    )
    parser.add_argument(
        "--draft",
        help="Path to the agent-authored digest JSON draft. If omitted, prints the agent task.",
    )
    parser.add_argument(
        "--task-output",
        help="Write the agent task prompt to this path instead of stdout.",
    )
    parser.add_argument(
        "--with-images",
        action="store_true",
        help="Print the default image-rich agent task. Kept for compatibility; this is now the default.",
    )
    parser.add_argument(
        "--text-only",
        action="store_true",
        help="Print the legacy text-only digest task that preserves source image references.",
    )
    args = parser.parse_args()
    if args.with_images and args.text_only:
        parser.error("--with-images and --text-only cannot be combined")

    source_dir = resolve_project(args.project)

    if not args.draft:
        task = build_agent_task(source_dir, with_images=not args.text_only)
        if args.task_output:
            output_path = Path(args.task_output).expanduser().resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(task, encoding="utf-8")
            print(f"Wrote {output_path}")
        else:
            print(task)
        return 0

    draft = read_draft(Path(args.draft).expanduser().resolve())
    digest_dir, digest_id, manifest = materialize_digest_project(source_dir, draft)
    print(json.dumps({
        "job_id": digest_id,
        "folder": digest_dir.name,
        "path": str(digest_dir),
        "title": manifest["title"],
        # Local dev convenience; use the dashboard Tailscale link when sharing across machines.
        "reader": f"http://localhost:3001/reader/{digest_id}",
    }, indent=2))
    return 0


def build_agent_task(source_dir: Path, with_images: bool = False) -> str:
    archive = _read_json(source_dir / "archive.json")
    manifest = _read_json(source_dir / "manifest.json")
    transcript_path = source_dir / "transcript.json"
    source_transcript = _read_json(transcript_path) if transcript_path.exists() else None
    source_chapters = archive.get("archive", [])
    draft_path = source_dir / "generated" / "ai-digest-draft.json"
    command = f'python3 tools/create_ai_digest_version.py "{source_dir}" --draft "{draft_path}"'

    image_context_dir = ROOT / "docs" / "impeccable"
    if with_images:
        image_instruction = f"""4. Create one novel WebP teaching image per digest chapter, with a maximum of 6 total images.
   - Before drawing anything, choose an infographic style for the whole digest: "simple" or "premium". Use "simple" for quiet text-led card strips via .codex/skills/simple-infographic, or "premium" for image-led editorial card strips via .codex/skills/premium-infographic. If the human gave a preference, obey it; otherwise choose the style that best fits the material and record the choice in operator_image_note.
   - Premium style must use GPT Image 2 / GPT 2.0 image generation for the bitmap visual, not local vector-only placeholders. Simple style may use generated or deterministic visuals as long as it passes the quality bar.
   - Load the product design system and follow it. The Impeccable skill is required: run it with the design context in {image_context_dir} (PRODUCT.md and DESIGN.md), for example by exporting IMPECCABLE_CONTEXT_DIR="{image_context_dir}". Obey the "Generated Image Art Direction" section of DESIGN.md and pass its acceptance checklist for every image. The bar is premium product-marketing quality: one calm idea per card, a small eyebrow label, one bold tight headline (Inter, large and tight), generous whitespace, precise alignment, and a restrained palette where color comes from a single focal element. Choose light (white #ffffff or #f5f5f7) or dark (#000000 to #101012) for the whole digest and hold it. Use one Operator Blue #3b82f6 accent at most. Do not include robots, mascots, faces, neon, glow, holograms, 3D renders, rainbow palettes, gradient text, decorative drop shadows, generic clip-art, grids of identical tiles, fake plus buttons, carousel arrows, pagination dots, navigation controls, and never truncate or clip a label.
   - Keep the whole set consistent: all six images share one theme, type scale, accent, and card style.
   - Do not copy, crop, trace, or reuse source frames, screenshots, or YouTube thumbnails.
   - Use the source frame images only as evidence for the lesson.
   - Save each image as a .webp file under this source project's generated/ folder before materializing.
   - Reference each generated image from its chapter as "images": ["generated/<filename>.webp"].
   - If a chapter image cannot meet the design bar, ship fewer images and explain the gap in operator_image_note. Never ship an off-brand image to fill a slot.
   - If the lesson truly needs more than 6 images, keep the best 6-image digest and add operator_image_note explaining how many images would be needed and why.
5. Write JSON only to:"""
        draft_shape = """{
  "title": "Short no-fluff learning title",
  "changes_summary": ["Removed filler.", "Merged repeated concepts."],
  "operator_image_note": "Optional note if more than 6 images would improve the digest.",
  "chapters": [
    {
      "source_indices": [0, 1],
      "concept": "Concept name",
      "summary": "One-sentence overview.",
      "content": "Dense teaching text for AI agents.",
      "timestamp_start": 0,
      "timestamp_end": 120,
      "images": ["generated/chapter-01-concept.webp"]
    }
  ]
}"""
    else:
        image_instruction = """4. Preserve source_indices so the CLI can carry forward the original image references.
5. Write JSON only to:"""
        draft_shape = """{
  "title": "Short no-fluff learning title",
  "changes_summary": ["Removed filler.", "Merged repeated concepts."],
  "chapters": [
    {
      "source_indices": [0, 1],
      "concept": "Concept name",
      "summary": "One-sentence overview.",
      "content": "Dense teaching text for AI agents.",
      "timestamp_start": 0,
      "timestamp_end": 120
    }
  ]
}"""

    return f"""Create a Smart YouTube Reader AI digest draft for this project.

{DIGEST_AGENT_TASK}

Important workflow:
1. Read the archive text and inspect the actual attached frame images before deciding what to keep.
2. Cut intros, outros, sponsor chatter, repeated sections, hype, and low-value transitions.
3. Keep durable concepts, procedures, definitions, examples, caveats, and visual explanations.
{image_instruction}
   {draft_path}
6. Run:
   {command}

Project folder:
{source_dir}

Video title:
{manifest.get("title") or source_dir.name}

YouTube:
{manifest.get("url") or "(not available)"}

Draft JSON shape:
{draft_shape}

Source chapter payload:
{build_digest_user_prompt(source_chapters, include_generated_images=with_images, source_transcript=source_transcript)}
"""


def read_draft(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = _extract_json_object(raw)
    if not isinstance(parsed, dict):
        raise SystemExit("Digest draft must be a JSON object.")
    return parsed


if __name__ == "__main__":
    raise SystemExit(main())
