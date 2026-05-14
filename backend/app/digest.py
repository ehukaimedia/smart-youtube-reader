import json
import re
import shutil
import time
import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from .jobs import DATA_ROOT, JobStore, slugify


DIGEST_AGENT_TASK = (
    "Create a Smart YouTube Reader AI digest draft from a source project. "
    "Inspect archive text and attached frame images before deciding what to keep. "
    "Return JSON only with title, chapters, and changes_summary. "
    "Each chapter must include source_indices, concept, summary, content, "
    "timestamp_start, and timestamp_end. When the task asks for generated images, "
    "write image files under generated/ and reference those paths from chapter images."
)

FLUFF_PATTERNS = [
    "like and subscribe",
    "smash the like",
    "hit subscribe",
    "welcome back",
    "without further ado",
    "before we start",
    "link in the description",
    "sponsor",
    "sponsored",
    "merch",
    "discord",
]


def create_digest_version_from_draft(
    job_store: JobStore | None,
    source_project: str | Path,
    draft_path: str | Path,
) -> dict[str, Any]:
    source_dir = resolve_project(source_project)
    draft = _read_json(Path(draft_path).expanduser().resolve())
    digest_dir, digest_id, manifest = materialize_digest_project(source_dir, draft)

    if job_store is not None:
        job_store.register_completed_job(
            job_id=digest_id,
            video_url=manifest["url"],
            data_dir=digest_dir,
            title=manifest["title"],
            created_at=manifest["created_at"],
            video_ext=manifest["video_ext"],
            kind="ai_digest",
            source_job_id=manifest.get("source_job_id"),
            digest_model=manifest.get("digest_model"),
            summary_image=manifest.get("summary_image"),
            media_policy=manifest.get("media_policy"),
        )

    return {
        "job_id": digest_id,
        "folder": digest_dir.name,
        "path": str(digest_dir),
        "title": manifest["title"],
        "archive_chapters": manifest["archive_chapters"],
    }


def materialize_digest_project(source_dir: Path, draft: dict[str, Any]) -> tuple[Path, str, dict[str, Any]]:
    source_dir = source_dir.resolve()
    archive_path = source_dir / "archive.json"
    manifest_path = source_dir / "manifest.json"
    if not archive_path.exists():
        raise HTTPException(status_code=404, detail=f"Archive file not found: {archive_path}")
    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail=f"Manifest file not found: {manifest_path}")

    source_archive = _read_json(archive_path)
    source_manifest = _read_json(manifest_path)
    source_chapters = source_archive.get("archive", [])
    if not source_chapters:
        raise HTTPException(status_code=400, detail="Source project has no archive chapters")

    digest_chapters, changes_summary, title_suggestion = normalize_digest_draft(
        source_dir=source_dir,
        source_chapters=source_chapters,
        draft=draft,
    )

    digest_title = _no_fluff_title(title_suggestion, digest_chapters)
    digest_id = str(uuid.uuid4())
    digest_dir = _unique_digest_dir(digest_title, digest_id)
    shutil.copytree(source_dir, digest_dir, ignore=shutil.ignore_patterns("__pycache__"))

    source_job_id = source_manifest.get("job_id") or source_archive.get("job_id")
    created_at = time.time()
    archive_data = {
        "job_id": digest_id,
        "folder": digest_dir.name,
        "kind": "ai_digest",
        "source_job_id": source_job_id,
        "source_folder": source_dir.name,
        "digest_model": "external-agent-cli",
        "digest_agent_status": "external_agent",
        "created_at": created_at,
        "digest_created_at": created_at,
        "archive": digest_chapters,
        "changes_summary": changes_summary,
        "transcript_policy": "digest_transcript_only",
    }
    generated_images = _collect_digest_generated_images(digest_chapters)
    operator_image_note = str(draft.get("operator_image_note") or "").strip()
    summary_image = generated_images[0] if generated_images else source_manifest.get("summary_image")

    manifest = {
        **source_manifest,
        "job_id": digest_id,
        "url": source_manifest.get("url", ""),
        "title": digest_title,
        "created_at": created_at,
        "status": "complete",
        "kind": "ai_digest",
        "source_job_id": source_job_id,
        "source_folder": source_dir.name,
        "digest_model": "external-agent-cli",
        "digest_agent_status": "external_agent",
        "digest_created_at": created_at,
        "archive_chapters": len(digest_chapters),
        "changes_summary": changes_summary,
        "transcript_policy": "digest_transcript_only",
        "video_ext": source_manifest.get("video_ext", "mp4"),
    }
    if generated_images:
        _prune_generated_image_digest(digest_dir, generated_images)
        manifest["generated_images"] = generated_images
        manifest["video_ext"] = None
        manifest["media_policy"] = "lightweight_generated_images_only"
        manifest["image_policy"] = (
            "AI digest chapter images use one unique generated teaching image per chapter, "
            "with a maximum of 6 images. Original source frames are used as evidence only "
            "and are not copied into the derived digest project."
        )
        archive_data["generated_images"] = generated_images
        archive_data["media_policy"] = manifest["media_policy"]
        archive_data["image_policy"] = manifest["image_policy"]
    if operator_image_note:
        manifest["operator_image_note"] = operator_image_note
        archive_data["operator_image_note"] = operator_image_note
    if summary_image:
        manifest["summary_image"] = summary_image
        archive_data["summary_image"] = summary_image

    _write_json(digest_dir / "archive.json", archive_data)
    _write_json(digest_dir / "manifest.json", manifest)
    _write_json(digest_dir / "transcript.json", _build_digest_transcript(digest_chapters))
    return digest_dir, digest_id, manifest


def normalize_digest_draft(
    source_dir: Path,
    source_chapters: list[dict[str, Any]],
    draft: dict[str, Any],
) -> tuple[list[dict[str, Any]], list[str], str]:
    chapters = draft.get("chapters", [])
    if not isinstance(chapters, list) or not chapters:
        raise RuntimeError("Digest draft must include a non-empty chapters array")

    changes = draft.get("changes_summary", [])
    if not isinstance(changes, list):
        raise RuntimeError("Digest draft changes_summary must be an array")
    changes = [str(item).strip() for item in changes[:12] if str(item).strip()]
    if not changes:
        raise RuntimeError("Digest draft must include a non-empty changes_summary")

    title = str(draft.get("title") or "").strip()
    if not title:
        raise RuntimeError("Digest draft must include a title")

    digest_chapters = []
    errors = []
    for index, chapter in enumerate(chapters):
        try:
            normalized = _normalize_agent_chapter(source_dir, source_chapters, chapter, strict=True)
        except RuntimeError as exc:
            errors.append(f"chapter {index + 1}: {exc}")
            continue
        if normalized:
            digest_chapters.append(normalized)

    if errors and not digest_chapters:
        raise RuntimeError("Digest draft returned no usable chapters: " + "; ".join(errors[:3]))

    try:
        _validate_digest_quality(digest_chapters, source_chapters)
    except RuntimeError as exc:
        if errors:
            raise RuntimeError(f"{exc}; skipped malformed chapters: {'; '.join(errors[:3])}") from exc
        raise

    if errors:
        changes.append(f"Skipped {len(errors)} malformed draft chapter(s).")
    _validate_generated_image_policy(digest_chapters)
    return digest_chapters, changes, title


def build_digest_user_prompt(source_chapters: list[dict[str, Any]], include_generated_images: bool = False) -> str:
    source_payload = []
    for index, chapter in enumerate(source_chapters):
        source_payload.append({
            "index": index,
            "concept": chapter.get("concept", ""),
            "summary": chapter.get("summary", ""),
            "content": _truncate(str(chapter.get("content", "")), 1800),
            "timestamp_start": chapter.get("timestamp_start", 0),
            "timestamp_end": chapter.get("timestamp_end"),
            "image_count": len(chapter.get("images", []) or []),
        })

    if include_generated_images:
        image_instruction = (
            "Each output chapter must also include exactly one generated image path in "
            'images, using the shape "images":["generated/chapter-01-concept.png"]. '
            "Use at most 6 output chapters/images. If more images would improve the lesson, "
            "add operator_image_note at the top level."
        )
        shape = (
            '{"title":"Plain Learning Title","chapters":[{"source_indices":[0,1],"concept":"Concept",'
            '"summary":"One sentence.","content":"Teaching text.","timestamp_start":0,"timestamp_end":120,'
            '"images":["generated/chapter-01-concept.png"]}],'
            '"changes_summary":["Removed filler.","Merged repeated concepts."],'
            '"operator_image_note":"Optional note for the operator."}'
        )
    else:
        image_instruction = "Use source_indices to preserve the original images attached to the kept source chapters."
        shape = (
            '{"title":"Plain Learning Title","chapters":[{"source_indices":[0,1],"concept":"Concept",'
            '"summary":"One sentence.","content":"Teaching text.","timestamp_start":0,"timestamp_end":120}],'
            '"changes_summary":["Removed filler.","Merged repeated concepts."]}'
        )

    return (
        "Build the digest from these source chapters. Each output chapter must include: "
        "source_indices, concept, summary, content, timestamp_start, timestamp_end. "
        "source_indices must be an array of integer indexes only, never text labels. "
        "Preserve every numeric claim, proper noun, dataset/benchmark name, and concrete "
        "example from the source content; cut filler and connective prose, not specifics. "
        "Merge tightly related source chapters where it improves the lesson; aim for "
        "roughly 60-80 percent of the source chapter count unless the material is already terse. "
        f"{image_instruction} "
        f"Do not include markdown fences or commentary. Required shape: {shape}\n\n"
        f"{json.dumps(source_payload, ensure_ascii=False)}"
    )


def resolve_project(value: str | Path) -> Path:
    candidate = Path(value).expanduser()
    if candidate.exists():
        return candidate.resolve()

    candidate = DATA_ROOT / str(value)
    if candidate.exists():
        return candidate.resolve()

    if DATA_ROOT.exists():
        for manifest_path in DATA_ROOT.glob("*/manifest.json"):
            try:
                manifest = _read_json(manifest_path)
            except Exception:
                continue
            if manifest.get("job_id") == str(value):
                return manifest_path.parent.resolve()

    raise HTTPException(status_code=404, detail=f"Project not found: {value}")


def _extract_json_object(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start < 0 or end <= start:
        raise RuntimeError("Digest draft did not contain JSON")
    try:
        parsed = json.loads(cleaned[start:end])
    except json.JSONDecodeError as exc:
        raise RuntimeError("Digest draft did not contain valid JSON") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("Digest draft must be a JSON object")
    return parsed


def _normalize_agent_chapter(
    source_dir: Path,
    source_chapters: list[dict[str, Any]],
    chapter: dict[str, Any],
    strict: bool = False,
) -> dict[str, Any] | None:
    if not isinstance(chapter, dict):
        if strict:
            raise RuntimeError("Digest chapter must be a JSON object")
        return None

    indices = chapter.get("source_indices", [])
    if not isinstance(indices, list):
        if strict:
            raise RuntimeError("Digest chapter has invalid source_indices")
        indices = []
    invalid_indices = [idx for idx in indices if not isinstance(idx, int) or idx < 0 or idx >= len(source_chapters)]
    valid_indices = [idx for idx in indices if isinstance(idx, int) and 0 <= idx < len(source_chapters)]
    if strict and (not indices or invalid_indices or len(valid_indices) != len(indices)):
        raise RuntimeError(f"Digest chapter has invalid source_indices: {indices}")
    if not valid_indices:
        valid_indices = [_nearest_chapter_index(source_chapters, chapter.get("timestamp_start", 0))]

    source_group = [source_chapters[idx] for idx in valid_indices]
    content = _compact_content(str(chapter.get("content") or " ".join(str(c.get("content", "")) for c in source_group)))
    if not content:
        if strict:
            raise RuntimeError("Digest chapter has empty content")
        return None

    if strict:
        raw_start = chapter.get("timestamp_start")
        raw_end = chapter.get("timestamp_end")
        if not isinstance(raw_start, (int, float)) or not isinstance(raw_end, (int, float)):
            raise RuntimeError("Digest chapter timestamps must be numeric")
        if raw_end < raw_start:
            raise RuntimeError("Digest chapter timestamp_end precedes timestamp_start")

    start = _to_float(chapter.get("timestamp_start"), source_group[0].get("timestamp_start", 0))
    end = _to_float(chapter.get("timestamp_end"), source_group[-1].get("timestamp_end", start + 60))
    agent_images = _collect_agent_images(source_dir, chapter, strict=strict)
    images = agent_images if agent_images is not None else _collect_source_images(source_group)
    image_review = {
        "mode": "agent_generated" if agent_images is not None else "human_curated",
        "kept": len(images),
        "note": (
            "Images were generated by the digest agent from the new digest chapter."
            if agent_images is not None
            else "Images are preserved from kept source chapters. Human review handles removal or replacement."
        ),
    }

    return {
        "concept": str(chapter.get("concept") or source_group[0].get("concept") or "AI Digest Chapter"),
        "summary": str(chapter.get("summary") or source_group[0].get("summary") or "")[:500],
        "content": content,
        "timestamp_start": start,
        "timestamp_end": max(end, start),
        "images": images,
        "source_indices": valid_indices,
        "image_review": image_review,
    }


def _validate_digest_quality(digest_chapters: list[dict[str, Any]], source_chapters: list[dict[str, Any]]) -> None:
    if not digest_chapters:
        raise RuntimeError("Digest draft returned no usable chapters")
    if len(source_chapters) > 3 and len(digest_chapters) >= len(source_chapters):
        raise RuntimeError("Digest draft did not reduce chapter count")

    content_lengths = [len(str(chapter.get("content") or "")) for chapter in digest_chapters]
    if any(length < 120 for length in content_lengths):
        raise RuntimeError("Digest draft returned chapter content that is too short")
    if sum(content_lengths) / len(content_lengths) < 240:
        raise RuntimeError("Digest draft returned average chapter content that is too thin")


def _read_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _unique_digest_dir(title: str, digest_id: str) -> Path:
    base_name = f"{slugify(title) or 'ai-digest'}_{digest_id[:8]}"
    candidate = DATA_ROOT / base_name
    counter = 2
    while candidate.exists():
        candidate = DATA_ROOT / f"{base_name}-{counter}"
        counter += 1
    return candidate


def _no_fluff_title(suggestion: str, digest_chapters: list[dict[str, Any]]) -> str:
    candidates = [suggestion]
    candidates.extend(str(chapter.get("concept", "")) for chapter in digest_chapters[:3])

    for candidate in candidates:
        cleaned = _clean_title(candidate)
        if cleaned and not _is_fluff(cleaned.lower()):
            return cleaned

    return "AI Learning Digest"


def _clean_title(title: str) -> str:
    title = re.sub(r"\[[^\]]*\]|\([^\)]*\)", " ", title)
    title = re.sub(r"\b(ultimate|insane|secret|shocking|must watch|you won't believe|complete guide)\b", " ", title, flags=re.IGNORECASE)
    title = re.sub(r"\b(ai digest|smart reader|youtube)\b", " ", title, flags=re.IGNORECASE)
    title = re.sub(r"[!?|]+", " ", title)
    title = re.sub(r"\s+", " ", title).strip(" -:_")
    words = title.split()
    if len(words) > 10:
        title = " ".join(words[:10])
    return title[:90].strip()


def _collect_source_images(source_chapters: list[dict[str, Any]]) -> list[str]:
    images: list[str] = []
    for chapter in source_chapters:
        for image in chapter.get("images", []) or []:
            if image and image not in images:
                images.append(image)
    return images


def _collect_agent_images(source_dir: Path, chapter: dict[str, Any], strict: bool = False) -> list[str] | None:
    raw_images = chapter.get("images")
    if raw_images is None:
        return None
    if not isinstance(raw_images, list):
        if strict:
            raise RuntimeError("Digest chapter images must be an array")
        return None

    images = [str(image).strip() for image in raw_images if str(image).strip()]
    if not images:
        if strict:
            raise RuntimeError("Generated-image digest chapters must include one image")
        return []
    if len(images) != 1:
        raise RuntimeError("Generated-image digest chapters must include exactly one image")

    image = images[0]
    path = Path(image)
    if path.is_absolute() or ".." in path.parts or path.parts[0] != "generated":
        raise RuntimeError("Generated digest images must use safe generated/<filename> paths")
    if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
        raise RuntimeError("Generated digest images must be PNG, JPG, JPEG, or WEBP files")
    if not (source_dir / path).is_file():
        raise RuntimeError(f"Generated digest image does not exist: {image}")
    return [image]


def _collect_digest_generated_images(digest_chapters: list[dict[str, Any]]) -> list[str]:
    images: list[str] = []
    for chapter in digest_chapters:
        for image in chapter.get("images", []) or []:
            if isinstance(image, str) and image.startswith("generated/") and image not in images:
                images.append(image)
    return images


def _validate_generated_image_policy(digest_chapters: list[dict[str, Any]]) -> None:
    generated_counts = [
        len([image for image in chapter.get("images", []) or [] if isinstance(image, str) and image.startswith("generated/")])
        for chapter in digest_chapters
    ]
    if not any(generated_counts):
        return
    if any(count != 1 for count in generated_counts):
        raise RuntimeError("Generated-image digest drafts must include exactly one generated image per chapter")
    if sum(generated_counts) > 6:
        raise RuntimeError("Generated-image digest drafts may include at most 6 images")


def _prune_generated_image_digest(digest_dir: Path, generated_images: list[Any]) -> None:
    keep = set()
    for image in generated_images:
        if isinstance(image, dict):
            image = image.get("path")
        if isinstance(image, str) and image:
            keep.add(Path(image))

    for relative in ("frames", "slices"):
        shutil.rmtree(digest_dir / relative, ignore_errors=True)

    for relative in ("frames.json",):
        (digest_dir / relative).unlink(missing_ok=True)

    for path in digest_dir.iterdir():
        if path.is_file() and path.suffix.lower() in {".mp4", ".webm", ".mkv", ".mov", ".m4v"}:
            path.unlink(missing_ok=True)

    generated_dir = digest_dir / "generated"
    if not generated_dir.exists():
        return

    for path in sorted(generated_dir.rglob("*"), reverse=True):
        relative = path.relative_to(digest_dir)
        if path.is_file() and relative not in keep:
            path.unlink(missing_ok=True)
        elif path.is_dir():
            try:
                path.rmdir()
            except OSError:
                pass


def _build_digest_transcript(digest_chapters: list[dict[str, Any]]) -> list[dict[str, Any]]:
    transcript = []
    for chapter in digest_chapters:
        start = _to_float(chapter.get("timestamp_start"), 0)
        end = max(_to_float(chapter.get("timestamp_end"), start), start)
        text = str(chapter.get("content") or chapter.get("summary") or chapter.get("concept") or "").strip()
        transcript.append({
            "text": text,
            "start": start,
            "duration": max(0.0, end - start),
        })
    return transcript


def _compact_content(content: str) -> str:
    sentences = re.split(r"(?<=[.!?])\s+", content.replace("\n", " ").strip())
    kept = []
    for sentence in sentences:
        lowered = sentence.lower()
        if any(pattern in lowered for pattern in FLUFF_PATTERNS):
            continue
        if sentence:
            kept.append(sentence)

    compacted = " ".join(kept) if kept else content.strip()
    return _truncate(re.sub(r"\s+", " ", compacted), 1800)


def _is_fluff(text: str) -> bool:
    return any(pattern in text for pattern in FLUFF_PATTERNS)


def _truncate(text: str, limit: int) -> str:
    text = re.sub(r"\s+", " ", text).strip()
    if len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0] + "..."


def _to_float(value: Any, default: Any) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        try:
            return float(default)
        except (TypeError, ValueError):
            return 0.0


def _nearest_chapter_index(source_chapters: list[dict[str, Any]], timestamp: Any) -> int:
    target = _to_float(timestamp, 0)
    return min(
        range(len(source_chapters)),
        key=lambda index: abs(_to_float(source_chapters[index].get("timestamp_start"), 0) - target),
    )
