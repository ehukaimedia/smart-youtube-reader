#!/usr/bin/env python3
"""Create a group AI digest project from an external agent-authored draft."""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import sys
import time
import uuid
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from backend.app.digest import (  # noqa: E402
    _clean_title,
    _compact_content,
    _extract_digest_preservation_items,
    _extract_json_object,
    _read_json,
    _write_json,
    resolve_project,
)
from backend.app.jobs import DATA_ROOT, slugify  # noqa: E402


IMAGE_COUNT = 3
NOVELTY_NGRAM_SIZE = 10
MAX_SOURCE_NGRAM_OVERLAP = 0.38


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a Smart YouTube Reader group AI digest from multiple source projects."
    )
    parser.add_argument(
        "projects",
        nargs="+",
        help="Two or more project folder paths, data/jobs folder names, or job IDs.",
    )
    parser.add_argument(
        "--draft",
        help="Path to the agent-authored group digest JSON draft. If omitted, prints the agent task.",
    )
    parser.add_argument(
        "--title",
        help="Optional working title for the group task.",
    )
    parser.add_argument(
        "--task-output",
        help="Write the agent task prompt to this path instead of stdout.",
    )
    args = parser.parse_args()

    source_dirs = [resolve_project(project) for project in args.projects]
    if len(source_dirs) < 2:
        raise SystemExit("Group digest requires at least two source projects.")

    if not args.draft:
        task = build_group_agent_task(source_dirs, args.title)
        if args.task_output:
            output_path = Path(args.task_output).expanduser().resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            output_path.write_text(task, encoding="utf-8")
            print(f"Wrote {output_path}")
        else:
            print(task)
        return 0

    draft_path = Path(args.draft).expanduser().resolve()
    draft = read_draft(draft_path)
    digest_dir, digest_id, manifest = materialize_group_digest_project(source_dirs, draft_path, draft)
    print(json.dumps({
        "job_id": digest_id,
        "folder": digest_dir.name,
        "path": str(digest_dir),
        "title": manifest["title"],
        "reader": f"http://localhost:3001/reader/{digest_id}",
    }, indent=2))
    return 0


def build_group_agent_task(source_dirs: list[Path], title: str | None = None) -> str:
    staging_dir = group_staging_dir(source_dirs, title)
    generated_dir = staging_dir / "generated"
    generated_dir.mkdir(parents=True, exist_ok=True)
    draft_path = staging_dir / "group-ai-digest-draft.json"
    command_projects = " ".join(f'"{source_dir}"' for source_dir in source_dirs)
    command = f'python3 tools/create_group_ai_digest_version.py {command_projects} --draft "{draft_path}"'
    source_payload = build_source_payload(source_dirs)

    return f"""Create a Smart YouTube Reader GROUP AI digest using the local CLI.

You are the digest agent. Do not use an in-app model option.

Goal:
Create one novel, intuitive combined transcript and exactly {IMAGE_COUNT} novel WebP teaching images from the selected source projects.

Teaching contract:
- Do not concatenate or lightly paraphrase the source transcripts.
- Synthesize a new mental model that teaches durable facts, theory, and testable hypotheses.
- Each chapter must help an AI agent understand what is true, why it works, when it might fail, and what evidence would confirm or reject it.
- Preserve every numeric claim, proper noun, dataset/benchmark name, named team/company, and concrete example that materially supports the combined lesson.
- Each source chapter includes preservation_items. Use them as a merge checklist, especially when many chapters collapse into one group chapter.
- Prefer plain causal language over trading-video narration. Avoid "the speaker says" framing.

Critical image rule:
- Choose one infographic style for the whole group digest before creating images: "simple" via .codex/skills/simple-infographic or "premium" via .codex/skills/premium-infographic. Use premium for full-color, concept-adaptive visual-learning infographics when the combined lesson benefits from richer teaching imagery. If the human gave a preference, obey it; otherwise choose the style that best fits the material and record the choice in each image prompt.
- Premium style must use GPT Image 2 / GPT 2.0 image generation for the bitmap visual, not local vector-only placeholders.
- Premium images are not hard-gated to a carousel, blue-only accent, light/dark theme, or single template. Reverse-engineer the combined lesson and choose the composition and palette that best make the mental model memorable and pleasing to understand.
- Inspect the original frame images while researching.
- Do not copy source frames, YouTube thumbnails, screenshots, or original image paths into the output.
- The output project must use only {IMAGE_COUNT} newly generated WebP teaching images created from the new combined transcript.
- Static infographic images must not include fake plus buttons, carousel arrows, pagination dots, or navigation controls.
- If you cannot create the {IMAGE_COUNT} new image files, stop and do not materialize the project.

Workflow:
1. Read every source archive below.
2. Inspect the attached frame images for each source chapter before deciding what matters.
3. Merge repeated lessons across videos into one coherent transcript.
4. Cut fluff, sponsor chatter, intros/outros, repeated examples, and low-value transitions.
5. Write a novel group digest draft to:
   {draft_path}
6. Create exactly {IMAGE_COUNT} new WebP teaching images at:
   {generated_dir}/01-framework-map.webp
   {generated_dir}/02-decision-flow.webp
   {generated_dir}/03-execution-checklist.webp
7. Materialize the new group project:
   {command}
8. Verify the dashboard shows the new project with a Group AI Digest badge and the reader opens it.

Draft JSON shape:
{{
  "title": "Short no-fluff group title",
  "learning_objective": "One sentence explaining what the combined digest teaches.",
  "changes_summary": ["Merged repeated lessons.", "Created a novel transcript and three generated WebP teaching images."],
  "images": [
    {{
      "path": "generated/01-framework-map.webp",
      "title": "Framework Map",
      "alt": "Novel teaching image showing the combined framework",
      "prompt": "Short record of the image-generation intent"
    }},
    {{
      "path": "generated/02-decision-flow.webp",
      "title": "Decision Flow",
      "alt": "Novel teaching image showing decision flow",
      "prompt": "Short record of the image-generation intent"
    }},
    {{
      "path": "generated/03-execution-checklist.webp",
      "title": "Execution Checklist",
      "alt": "Novel teaching image showing execution checklist",
      "prompt": "Short record of the image-generation intent"
    }}
  ],
  "chapters": [
    {{
      "source_refs": [{{"project_index": 0, "chapter_indices": [1, 2]}}],
      "concept": "Concept name",
      "summary": "One-sentence overview.",
      "content": "Dense novel transcript text for AI agents.",
      "facts": ["Compact fact grounded in the sources.", "Another durable fact."],
      "theory": "Why these facts fit together into a reusable model.",
      "hypothesis": "A testable expectation or failure condition derived from the model.",
      "timestamp_start": 0,
      "timestamp_end": 120,
      "image_path": "generated/01-framework-map.webp"
    }}
  ]
}}

Source projects:
{source_payload}
"""


def build_source_payload(source_dirs: list[Path]) -> str:
    projects = []
    for project_index, source_dir in enumerate(source_dirs):
        archive = _read_json(source_dir / "archive.json")
        manifest = _read_json(source_dir / "manifest.json")
        chapters = []
        for chapter_index, chapter in enumerate(archive.get("archive", [])):
            images = []
            for image in chapter.get("images", []) or []:
                image_path = source_dir / image
                if image_path.exists():
                    images.append({
                        "path": image,
                        "local_path": str(image_path),
                    })
            chapters.append({
                "chapter_index": chapter_index,
                "concept": chapter.get("concept", ""),
                "summary": chapter.get("summary", ""),
                "content": _truncate_for_task(str(chapter.get("content", ""))),
                "timestamp_start": chapter.get("timestamp_start", 0),
                "timestamp_end": chapter.get("timestamp_end"),
                "images": images[:6],
                "preservation_items": _extract_digest_preservation_items(
                    " ".join([
                        str(chapter.get("concept", "")),
                        str(chapter.get("summary", "")),
                        str(chapter.get("content", "")),
                    ])
                ),
            })
        projects.append({
            "project_index": project_index,
            "title": manifest.get("title") or source_dir.name,
            "job_id": manifest.get("job_id"),
            "folder": source_dir.name,
            "youtube": manifest.get("url"),
            "archive_json": str(source_dir / "archive.json"),
            "chapters": chapters,
        })
    return json.dumps(projects, indent=2, ensure_ascii=False)


def read_draft(path: Path) -> dict[str, Any]:
    raw = path.read_text(encoding="utf-8")
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        parsed = _extract_json_object(raw)
    if not isinstance(parsed, dict):
        raise SystemExit("Group digest draft must be a JSON object.")
    return parsed


def materialize_group_digest_project(
    source_dirs: list[Path],
    draft_path: Path,
    draft: dict[str, Any],
) -> tuple[Path, str, dict[str, Any]]:
    source_archives = [_read_json(source_dir / "archive.json") for source_dir in source_dirs]
    source_manifests = [_read_json(source_dir / "manifest.json") for source_dir in source_dirs]
    source_text = collect_source_text(source_archives)
    normalized_images = normalize_group_images(draft_path, draft)
    normalized_chapters = normalize_group_chapters(draft, normalized_images, source_archives, source_text)
    title = _clean_title(str(draft.get("title") or "Group AI Digest")) or "Group AI Digest"
    source_titles = [manifest.get("title") or source_dirs[index].name for index, manifest in enumerate(source_manifests)]
    if title.lower() in {str(source_title).strip().lower() for source_title in source_titles}:
        raise SystemExit("Group digest title must be novel, not a source project title.")
    digest_id = str(uuid.uuid4())
    digest_dir = unique_group_digest_dir(title, digest_id)
    digest_dir.mkdir(parents=True)

    for image in normalized_images:
        source_image = (draft_path.parent / image["path"]).resolve()
        target_image = digest_dir / image["path"]
        target_image.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source_image, target_image)

    created_at = time.time()
    source_job_ids = [manifest.get("job_id") for manifest in source_manifests if manifest.get("job_id")]
    source_folders = [source_dir.name for source_dir in source_dirs]
    changes_summary = normalize_changes(draft.get("changes_summary"))
    learning_objective = normalize_teaching_string(draft.get("learning_objective"), "learning_objective", 40)
    transcript = build_transcript(normalized_chapters)
    archive_data = {
        "job_id": digest_id,
        "folder": digest_dir.name,
        "kind": "group_ai_digest",
        "source_job_ids": source_job_ids,
        "source_folders": source_folders,
        "source_titles": source_titles,
        "digest_model": "external-agent-cli",
        "digest_agent_status": "external_agent",
        "created_at": created_at,
        "digest_created_at": created_at,
        "archive": normalized_chapters,
        "changes_summary": changes_summary,
        "learning_objective": learning_objective,
        "generated_images": normalized_images,
        "summary_image": normalized_images[0]["path"],
        "image_policy": "Only novel generated WebP teaching images are included. Source frames were evidence only.",
    }
    manifest = {
        "job_id": digest_id,
        "url": "group://smart-youtube-reader",
        "title": title,
        "created_at": created_at,
        "status": "complete",
        "kind": "group_ai_digest",
        "source_job_ids": source_job_ids,
        "source_folders": source_folders,
        "source_titles": source_titles,
        "digest_model": "external-agent-cli",
        "digest_agent_status": "external_agent",
        "digest_created_at": created_at,
        "archive_chapters": len(normalized_chapters),
        "changes_summary": changes_summary,
        "learning_objective": learning_objective,
        "generated_images": normalized_images,
        "summary_image": normalized_images[0]["path"],
        "summary_image_source": "group_ai_generated",
        "video_ext": "none",
    }

    _write_json(digest_dir / "archive.json", archive_data)
    _write_json(digest_dir / "manifest.json", manifest)
    _write_json(digest_dir / "transcript.json", transcript)
    return digest_dir, digest_id, manifest


def normalize_group_images(draft_path: Path, draft: dict[str, Any]) -> list[dict[str, str]]:
    images = draft.get("images")
    if not isinstance(images, list) or len(images) != IMAGE_COUNT:
        raise SystemExit(f"Group digest draft must include exactly {IMAGE_COUNT} images.")

    normalized = []
    seen_paths = set()
    for index, image in enumerate(images):
        if not isinstance(image, dict):
            raise SystemExit("Each group image entry must be an object.")
        image_path = str(image.get("path") or "").strip()
        if not is_generated_image_path(image_path):
            raise SystemExit(f"Image {index + 1} must use a safe generated image path, not {image_path!r}.")
        if Path(image_path).suffix.lower() != ".webp":
            raise SystemExit(f"Image {index + 1} must use a generated/*.webp path, not {image_path!r}.")
        if image_path in seen_paths:
            raise SystemExit(f"Duplicate generated image path: {image_path}")
        source_image = (draft_path.parent / image_path).resolve()
        if not source_image.exists() or not source_image.is_file():
            raise SystemExit(f"Generated image file is missing: {source_image}")
        seen_paths.add(image_path)
        normalized.append({
            "path": image_path,
            "title": str(image.get("title") or f"Generated Image {index + 1}").strip(),
            "alt": str(image.get("alt") or "Generated group digest teaching image").strip(),
            "prompt": str(image.get("prompt") or "").strip(),
        })
        if len(normalized[-1]["prompt"]) < 30:
            raise SystemExit(f"Image {index + 1} prompt is too thin; record the teaching intent for the generated image.")
    return normalized


def normalize_group_chapters(
    draft: dict[str, Any],
    normalized_images: list[dict[str, str]],
    source_archives: list[dict[str, Any]],
    source_text: str,
) -> list[dict[str, Any]]:
    chapters = draft.get("chapters")
    if not isinstance(chapters, list) or not chapters:
        raise SystemExit("Group digest draft must include a non-empty chapters array.")

    valid_image_paths = {image["path"] for image in normalized_images}
    normalized = []
    for index, chapter in enumerate(chapters):
        if not isinstance(chapter, dict):
            raise SystemExit(f"Chapter {index + 1} must be an object.")
        content = _compact_content(str(chapter.get("content") or ""))
        if len(content) < 240:
            raise SystemExit(f"Chapter {index + 1} content is too thin.")
        if source_ngram_overlap(content, source_text) > MAX_SOURCE_NGRAM_OVERLAP:
            raise SystemExit(f"Chapter {index + 1} is too extractive; rewrite it as a novel transcript.")
        facts = normalize_facts(chapter.get("facts"), index)
        theory = normalize_teaching_string(chapter.get("theory"), f"chapter {index + 1} theory", 90)
        hypothesis = normalize_teaching_string(chapter.get("hypothesis"), f"chapter {index + 1} hypothesis", 80)
        image_path = str(chapter.get("image_path") or normalized_images[index % IMAGE_COUNT]["path"]).strip()
        if image_path not in valid_image_paths:
            raise SystemExit(f"Chapter {index + 1} image_path must reference one of the three generated images.")
        start = to_float(chapter.get("timestamp_start"), index * 120)
        end = to_float(chapter.get("timestamp_end"), start + 120)
        refs = normalize_source_refs(chapter.get("source_refs"), source_archives)
        normalized.append({
            "concept": str(chapter.get("concept") or f"Group Lesson {index + 1}").strip(),
            "summary": str(chapter.get("summary") or "").strip()[:500],
            "content": content,
            "facts": facts,
            "theory": theory,
            "hypothesis": hypothesis,
            "timestamp_start": start,
            "timestamp_end": max(end, start),
            "images": [image_path],
            "source_refs": refs,
            "image_review": {
                "mode": "ai_generated_novel",
                "note": "This is a novel generated WebP teaching image for the group digest. Original source frames are not used in the output archive.",
            },
        })

    avg_content = sum(len(chapter["content"]) for chapter in normalized) / len(normalized)
    if avg_content < 320:
        raise SystemExit("Group digest draft average chapter content is too thin.")
    return normalized


def normalize_facts(value: Any, chapter_index: int) -> list[str]:
    if not isinstance(value, list):
        raise SystemExit(f"Chapter {chapter_index + 1} must include facts as an array.")
    facts = [str(item).strip() for item in value if str(item).strip()]
    if len(facts) < 2:
        raise SystemExit(f"Chapter {chapter_index + 1} needs at least two digestible facts.")
    if any(len(fact) < 24 for fact in facts[:2]):
        raise SystemExit(f"Chapter {chapter_index + 1} facts are too thin.")
    return facts[:6]


def normalize_teaching_string(value: Any, label: str, min_length: int) -> str:
    text = " ".join(str(value or "").split())
    if len(text) < min_length:
        raise SystemExit(f"{label} is too thin.")
    return text


def normalize_source_refs(value: Any, source_archives: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if not isinstance(value, list) or not value:
        raise SystemExit("Each group chapter must include source_refs.")
    refs = []
    for item in value:
        if not isinstance(item, dict):
            raise SystemExit("Each source_ref must be an object.")
        project_index = item.get("project_index")
        chapter_indices = item.get("chapter_indices")
        if not isinstance(project_index, int) or project_index < 0 or project_index >= len(source_archives):
            raise SystemExit(f"Invalid source_ref project_index: {project_index}")
        if not isinstance(chapter_indices, list) or not chapter_indices:
            raise SystemExit("source_ref chapter_indices must be a non-empty array.")
        max_index = len(source_archives[project_index].get("archive", [])) - 1
        cleaned_indices = []
        for chapter_index in chapter_indices:
            if not isinstance(chapter_index, int) or chapter_index < 0 or chapter_index > max_index:
                raise SystemExit(f"Invalid chapter index {chapter_index} for project {project_index}.")
            if chapter_index not in cleaned_indices:
                cleaned_indices.append(chapter_index)
        refs.append({
            "project_index": project_index,
            "chapter_indices": cleaned_indices,
        })
    return refs


def normalize_changes(value: Any) -> list[str]:
    if not isinstance(value, list):
        raise SystemExit("Group digest draft changes_summary must be an array.")
    changes = [str(item).strip() for item in value if str(item).strip()]
    if not changes:
        raise SystemExit("Group digest draft must include changes_summary.")
    return changes[:12]


def build_transcript(chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    lines = []
    for chapter in chapters:
        fact_text = " ".join(f"Fact: {fact}" for fact in chapter.get("facts", []))
        lines.append({
            "text": (
                f"{chapter['concept']}. {chapter['content']} "
                f"{fact_text} Theory: {chapter.get('theory', '')} "
                f"Hypothesis: {chapter.get('hypothesis', '')}"
            ),
            "start": chapter["timestamp_start"],
            "duration": max(1, chapter["timestamp_end"] - chapter["timestamp_start"]),
        })
    return lines


def is_generated_image_path(value: str) -> bool:
    if not value or Path(value).is_absolute():
        return False
    path = Path(value)
    if ".." in path.parts:
        return False
    if len(path.parts) < 2 or path.parts[0] != "generated":
        return False
    if any(part in {"frames", "slices"} for part in path.parts):
        return False
    return path.suffix.lower() in {".png", ".jpg", ".jpeg", ".webp"}


def group_staging_dir(source_dirs: list[Path], title: str | None) -> Path:
    seed = "|".join(str(source_dir.resolve()) for source_dir in source_dirs) + f"|{title or ''}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:10]
    label = slugify(title or "group-ai-digest") or "group-ai-digest"
    return ROOT / "data" / "group-digests" / f"{label}_{digest}"


def unique_group_digest_dir(title: str, digest_id: str) -> Path:
    base_name = f"{slugify(title) or 'group-ai-digest'}_{digest_id[:8]}"
    candidate = DATA_ROOT / base_name
    counter = 2
    while candidate.exists():
        candidate = DATA_ROOT / f"{base_name}-{counter}"
        counter += 1
    return candidate


def to_float(value: Any, default: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        try:
            return float(default)
        except (TypeError, ValueError):
            return 0.0


def _truncate_for_task(text: str, limit: int = 1400) -> str:
    text = " ".join(text.split())
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."


def collect_source_text(source_archives: list[dict[str, Any]]) -> str:
    parts = []
    for archive in source_archives:
        for chapter in archive.get("archive", []) or []:
            parts.append(str(chapter.get("content") or ""))
            parts.append(str(chapter.get("summary") or ""))
    return normalize_for_overlap(" ".join(parts))


def source_ngram_overlap(content: str, source_text: str) -> float:
    draft_tokens = normalize_for_overlap(content).split()
    source_tokens = source_text.split()
    if len(draft_tokens) < NOVELTY_NGRAM_SIZE or len(source_tokens) < NOVELTY_NGRAM_SIZE:
        return 0.0
    draft_ngrams = set(ngrams(draft_tokens, NOVELTY_NGRAM_SIZE))
    source_ngrams = set(ngrams(source_tokens, NOVELTY_NGRAM_SIZE))
    if not draft_ngrams:
        return 0.0
    return len(draft_ngrams & source_ngrams) / len(draft_ngrams)


def ngrams(tokens: list[str], size: int) -> list[tuple[str, ...]]:
    return [tuple(tokens[index:index + size]) for index in range(0, len(tokens) - size + 1)]


def normalize_for_overlap(text: str) -> str:
    normalized = []
    for char in text.lower():
        normalized.append(char if char.isalnum() or char.isspace() else " ")
    return " ".join("".join(normalized).split())


if __name__ == "__main__":
    raise SystemExit(main())
