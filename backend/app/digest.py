import json
import os
import re
import shutil
import time
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

from fastapi import HTTPException

from .jobs import DATA_ROOT, JobStore, slugify


DIGEST_AGENT_MODELS = [
    {
        "id": "ollama:smart-youtube-digest",
        "label": "Local Gemma AI Digest",
        "provider": "ollama",
        "requires": "ollama:smart-youtube-digest",
    },
    {
        "id": "local:deterministic",
        "label": "Local deterministic digest",
        "provider": "local",
        "requires": None,
    },
]

MODEL_ALIASES = {
    "gemma4": "ollama:smart-youtube-digest",
    "gemma4:latest": "ollama:smart-youtube-digest",
    "smart-youtube-digest": "ollama:smart-youtube-digest",
    "ollama:gemma4": "ollama:smart-youtube-digest",
    "ollama:gemma4:latest": "ollama:smart-youtube-digest",
}

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

DIGEST_SYSTEM_PROMPT = (
    "You are a local editor agent for Smart YouTube Reader. "
    "Create a compact AI learning digest from a YouTube archive. "
    "Cut intros, outros, sponsor chatter, repetition, hype, and low-value transitions. "
    "Keep durable concepts, procedures, definitions, examples, and caveats. "
    "Return only JSON with keys title, chapters, and changes_summary. "
    "changes_summary must be a non-empty array of short strings. "
    "The title must be a short no-fluff learning title, not a YouTube headline. "
    "Do not remove, replace, or judge images; humans curate images separately."
)


def get_digest_agent_models() -> list[dict[str, Any]]:
    return [
        {
            **model,
            "available": _is_digest_model_available(model),
        }
        for model in DIGEST_AGENT_MODELS
    ]


def _is_digest_model_available(model: dict[str, Any]) -> bool:
    if not model["requires"]:
        return True
    if model["provider"] == "ollama":
        return _ollama_model_available(model["id"].split(":", 1)[1])
    return bool(os.environ.get(model["requires"]))


def create_digest_version(
    job_store: JobStore,
    job_id: str,
    model: str | None,
):
    try:
        source_job = job_store.get(job_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Job not found")

    if not source_job.data_dir or not source_job.data_dir.exists():
        raise HTTPException(status_code=404, detail="Project files not found")

    source_dir = source_job.data_dir.resolve()
    archive_path = source_dir / "archive.json"
    manifest_path = source_dir / "manifest.json"
    if not archive_path.exists():
        raise HTTPException(status_code=404, detail="Archive file not found")

    source_archive = _read_json(archive_path)
    source_manifest = _read_json(manifest_path) if manifest_path.exists() else {}
    source_chapters = source_archive.get("archive", [])
    if not source_chapters:
        raise HTTPException(status_code=400, detail="Source project has no archive chapters")

    try:
        selected_model = _normalize_model(model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    changes_summary: list[str] = []
    title_suggestion = ""
    if selected_model == "local:deterministic":
        digest_chapters, changes_summary = _generate_deterministic_digest(source_dir, source_chapters)
        agent_status = "deterministic"
        if not digest_chapters:
            digest_chapters, changes_summary = _generate_deterministic_digest(source_dir, source_chapters, keep_at_least_one=True)
    else:
        try:
            digest_chapters, changes_summary, title_suggestion = _generate_agent_digest(
                source_dir=source_dir,
                source_chapters=source_chapters,
                selected_model=selected_model,
            )
            agent_status = "agent"
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"AI digest agent failed for {selected_model}: {exc}",
            ) from exc

        if not digest_chapters:
            raise HTTPException(
                status_code=502,
                detail=f"AI digest agent returned no chapters for {selected_model}",
            )

    digest_title = _no_fluff_title(title_suggestion, digest_chapters)
    digest_id = str(uuid.uuid4())
    digest_dir = _unique_digest_dir(digest_title, digest_id)
    shutil.copytree(source_dir, digest_dir, ignore=shutil.ignore_patterns("__pycache__"))

    created_at = time.time()
    archive_data = {
        "job_id": digest_id,
        "folder": digest_dir.name,
        "kind": "ai_digest",
        "source_job_id": source_job.id,
        "source_folder": source_dir.name,
        "digest_model": selected_model,
        "digest_agent_status": agent_status,
        "created_at": created_at,
        "digest_created_at": created_at,
        "archive": digest_chapters,
        "changes_summary": changes_summary,
    }
    _write_json(digest_dir / "archive.json", archive_data)

    manifest = {
        **source_manifest,
        "job_id": digest_id,
        "url": source_job.payload.video_url or source_manifest.get("url", ""),
        "title": digest_title,
        "created_at": created_at,
        "status": "complete",
        "kind": "ai_digest",
        "source_job_id": source_job.id,
        "source_folder": source_dir.name,
        "digest_model": selected_model,
        "digest_agent_status": agent_status,
        "digest_created_at": created_at,
        "archive_chapters": len(digest_chapters),
        "changes_summary": changes_summary,
        "video_ext": source_job.video_ext or source_manifest.get("video_ext", "mp4"),
    }
    _write_json(digest_dir / "manifest.json", manifest)

    return job_store.register_completed_job(
        job_id=digest_id,
        video_url=manifest["url"],
        data_dir=digest_dir,
        title=digest_title,
        created_at=created_at,
        video_ext=manifest["video_ext"],
        kind="ai_digest",
        source_job_id=source_job.id,
        digest_model=selected_model,
    )


def _read_json(path: Path) -> dict[str, Any]:
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _write_json(path: Path, data: dict[str, Any]) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _normalize_model(model: str | None) -> str:
    if not model or not model.strip():
        raise ValueError("Digest model is required")
    model = model.strip()
    normalized = MODEL_ALIASES.get(model, model)
    supported = {item["id"] for item in DIGEST_AGENT_MODELS}
    if normalized not in supported:
        raise ValueError(f"Unsupported digest model: {model}")
    return normalized


def _unique_digest_dir(title: str, digest_id: str) -> Path:
    base_name = f"{slugify(title) or 'ai-digest'}_{digest_id[:8]}"
    candidate = DATA_ROOT / base_name
    counter = 2
    while candidate.exists():
        candidate = DATA_ROOT / f"{base_name}-{counter}"
        counter += 1
    return candidate


def _generate_agent_digest(
    source_dir: Path,
    source_chapters: list[dict[str, Any]],
    selected_model: str,
) -> tuple[list[dict[str, Any]], list[str], str]:
    user_prompt = build_digest_user_prompt(source_chapters)

    if selected_model.startswith("ollama:"):
        raw = _call_ollama_agent(selected_model, DIGEST_SYSTEM_PROMPT, user_prompt)
    else:
        raise RuntimeError(f"Unsupported digest agent model: {selected_model}")

    parsed = _extract_json_object(raw)
    chapters = parsed.get("chapters", [])
    if not isinstance(chapters, list) or not chapters:
        raise RuntimeError("Digest agent returned invalid chapters")

    changes = parsed.get("changes_summary", [])
    if not isinstance(changes, list) or not changes:
        raise RuntimeError("Digest agent returned invalid changes_summary")
    changes = [str(item).strip() for item in changes[:12] if str(item).strip()]
    if not changes:
        raise RuntimeError("Digest agent returned empty changes_summary")

    title = str(parsed.get("title") or "").strip()
    if not title:
        raise RuntimeError("Digest agent returned an empty title")

    digest_chapters = []
    normalization_errors = []
    for index, chapter in enumerate(chapters):
        try:
            normalized = _normalize_agent_chapter(source_dir, source_chapters, chapter, strict=True)
        except RuntimeError as exc:
            normalization_errors.append(f"chapter {index + 1}: {exc}")
            continue
        if normalized:
            digest_chapters.append(normalized)

    if normalization_errors and not digest_chapters:
        raise RuntimeError("Digest agent returned no usable chapters: " + "; ".join(normalization_errors[:3]))

    try:
        _validate_digest_quality(digest_chapters, source_chapters)
    except RuntimeError as exc:
        if normalization_errors:
            raise RuntimeError(f"{exc}; skipped malformed agent chapters: {'; '.join(normalization_errors[:3])}") from exc
        raise

    if normalization_errors:
        changes.append(f"Skipped {len(normalization_errors)} malformed agent chapter(s).")
    return digest_chapters, changes, title


def build_digest_user_prompt(source_chapters: list[dict[str, Any]]) -> str:
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

    return (
        "Build the digest from these source chapters. Each output chapter must include: "
        "source_indices, concept, summary, content, timestamp_start, timestamp_end. "
        "source_indices must be an array of integer indexes only, never text labels. "
        "Use source_indices to preserve the original images attached to the kept source chapters. "
        "Do not include markdown fences or commentary. Required shape: "
        '{"title":"Plain Learning Title","chapters":[{"source_indices":[0,1],"concept":"Concept",'
        '"summary":"One sentence.","content":"Teaching text.","timestamp_start":0,"timestamp_end":120}],'
        '"changes_summary":["Removed filler.","Merged repeated concepts."]}\n\n'
        f"{json.dumps(source_payload, ensure_ascii=False)}"
    )


def _call_ollama_agent(selected_model: str, system_prompt: str, user_prompt: str) -> str:
    model = selected_model.split(":", 1)[1]
    body = json.dumps({
        "model": model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "stream": False,
        "options": {
            "temperature": 0.05,
            "num_ctx": 16384,
        },
    }).encode("utf-8")
    request = urllib.request.Request(
        os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/") + "/api/chat",
        data=body,
        method="POST",
        headers={
            "content-type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Ollama digest request failed: HTTP {exc.code}: {detail}") from exc
    except Exception as exc:
        raise RuntimeError(f"Ollama digest request failed: {exc}") from exc

    return str(payload.get("message", {}).get("content") or "")


def _ollama_model_available(model: str) -> bool:
    try:
        request = urllib.request.Request(
            os.environ.get("OLLAMA_HOST", "http://127.0.0.1:11434").rstrip("/") + "/api/tags",
            method="GET",
        )
        with urllib.request.urlopen(request, timeout=3) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except Exception:
        return False

    names = {item.get("name") for item in payload.get("models", [])}
    return model in names or f"{model}:latest" in names


def _extract_json_object(raw: str) -> dict[str, Any]:
    cleaned = raw.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

    start = cleaned.find("{")
    end = cleaned.rfind("}") + 1
    if start < 0 or end <= start:
        raise RuntimeError("Digest agent did not return JSON")
    try:
        parsed = json.loads(cleaned[start:end])
    except json.JSONDecodeError as exc:
        raise RuntimeError("Digest agent did not return valid JSON") from exc
    if not isinstance(parsed, dict):
        raise RuntimeError("Digest agent did not return a JSON object")
    return parsed


def _normalize_agent_chapter(
    source_dir: Path,
    source_chapters: list[dict[str, Any]],
    chapter: dict[str, Any],
    strict: bool = False,
) -> dict[str, Any] | None:
    if not isinstance(chapter, dict):
        if strict:
            raise RuntimeError("Digest agent chapter must be a JSON object")
        return None

    indices = chapter.get("source_indices", [])
    if not isinstance(indices, list):
        if strict:
            raise RuntimeError("Digest agent chapter has invalid source_indices")
        indices = []
    invalid_indices = [idx for idx in indices if not isinstance(idx, int) or idx < 0 or idx >= len(source_chapters)]
    valid_indices = [idx for idx in indices if isinstance(idx, int) and 0 <= idx < len(source_chapters)]
    if strict and (not indices or invalid_indices or len(valid_indices) != len(indices)):
        raise RuntimeError(f"Digest agent chapter has invalid source_indices: {indices}")
    if not valid_indices:
        valid_indices = [_nearest_chapter_index(source_chapters, chapter.get("timestamp_start", 0))]

    source_group = [source_chapters[idx] for idx in valid_indices]
    content = _compact_content(str(chapter.get("content") or " ".join(str(c.get("content", "")) for c in source_group)))
    if not content:
        if strict:
            raise RuntimeError("Digest agent chapter has empty content")
        return None

    if strict:
        raw_start = chapter.get("timestamp_start")
        raw_end = chapter.get("timestamp_end")
        if not isinstance(raw_start, (int, float)) or not isinstance(raw_end, (int, float)):
            raise RuntimeError("Digest agent chapter timestamps must be numeric")
        if raw_end < raw_start:
            raise RuntimeError("Digest agent chapter timestamp_end precedes timestamp_start")

    start = _to_float(chapter.get("timestamp_start"), source_group[0].get("timestamp_start", 0))
    end = _to_float(chapter.get("timestamp_end"), source_group[-1].get("timestamp_end", start + 60))
    images = _collect_source_images(source_group)

    return {
        "concept": str(chapter.get("concept") or source_group[0].get("concept") or "AI Digest Chapter"),
        "summary": str(chapter.get("summary") or source_group[0].get("summary") or "")[:500],
        "content": content,
        "timestamp_start": start,
        "timestamp_end": max(end, start),
        "images": images,
        "source_indices": valid_indices,
        "image_review": {
            "mode": "human_curated",
            "kept": len(images),
            "note": "Images are preserved from kept source chapters. Human review handles removal or replacement.",
        },
    }


def _validate_digest_quality(digest_chapters: list[dict[str, Any]], source_chapters: list[dict[str, Any]]) -> None:
    if not digest_chapters:
        raise RuntimeError("Digest agent returned no usable chapters")
    if len(source_chapters) > 3 and len(digest_chapters) >= len(source_chapters):
        raise RuntimeError("Digest agent did not reduce chapter count")

    content_lengths = [len(str(chapter.get("content") or "")) for chapter in digest_chapters]
    if any(length < 120 for length in content_lengths):
        raise RuntimeError("Digest agent returned chapter content that is too short")
    if sum(content_lengths) / len(content_lengths) < 240:
        raise RuntimeError("Digest agent returned average chapter content that is too thin")


def _generate_deterministic_digest(
    source_dir: Path,
    source_chapters: list[dict[str, Any]],
    keep_at_least_one: bool = False,
) -> tuple[list[dict[str, Any]], list[str]]:
    digest = []
    removed = 0
    for index, chapter in enumerate(source_chapters):
        content = _compact_content(str(chapter.get("content", "")))
        text_for_filter = " ".join([
            str(chapter.get("concept", "")),
            str(chapter.get("summary", "")),
            str(chapter.get("content", "")),
        ]).lower()
        if not keep_at_least_one and (_is_fluff(text_for_filter) or len(content) < 120):
            removed += 1
            continue

        images = _collect_source_images([chapter])
        digest.append({
            "concept": chapter.get("concept") or "AI Digest Chapter",
            "summary": chapter.get("summary") or "",
            "content": content,
            "timestamp_start": _to_float(chapter.get("timestamp_start"), 0),
            "timestamp_end": _to_float(chapter.get("timestamp_end"), chapter.get("timestamp_start", 0)),
            "images": images,
            "source_indices": [index],
            "image_review": {
                "mode": "human_curated",
                "kept": len(images),
                "note": "Images are preserved from kept source chapters. Human review handles removal or replacement.",
            },
        })

    if not digest and keep_at_least_one and source_chapters:
        return _generate_deterministic_digest(source_dir, source_chapters[:1], keep_at_least_one=True)

    changes = [
        f"Removed {removed} low-value or filler chapter(s).",
        "Compacted chapter text for agent learning context.",
        "Preserved image references from kept source chapters for human curation.",
    ]
    return digest, changes


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
