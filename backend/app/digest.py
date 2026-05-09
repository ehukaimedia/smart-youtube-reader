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
from PIL import Image, ImageStat

from .jobs import DATA_ROOT, JobStore, slugify


DIGEST_AGENT_MODELS = [
    {
        "id": "openai:gpt-5.5",
        "label": "Headless GPT 5.5",
        "provider": "openai",
        "requires": "OPENAI_API_KEY",
    },
    {
        "id": "anthropic:claude-opus-4-7",
        "label": "Headless Opus 4.7",
        "provider": "anthropic",
        "requires": "ANTHROPIC_API_KEY",
    },
    {
        "id": "local:deterministic",
        "label": "Local deterministic digest",
        "provider": "local",
        "requires": None,
    },
]

MODEL_ALIASES = {
    "gpt-5.5": "openai:gpt-5.5",
    "headless-gpt-5.5": "openai:gpt-5.5",
    "opus-4.7": "anthropic:claude-opus-4-7",
    "claude-opus-4.7": "anthropic:claude-opus-4-7",
    "claude-opus-4-7": "anthropic:claude-opus-4-7",
    "anthropic:claude-opus-4.7": "anthropic:claude-opus-4-7",
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


def get_digest_agent_models() -> list[dict[str, Any]]:
    return [
        {
            **model,
            "available": not model["requires"] or bool(os.environ.get(model["requires"])),
        }
        for model in DIGEST_AGENT_MODELS
    ]


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

    system_prompt = (
        "You are a headless editor agent for Smart YouTube Reader. "
        "Create a compact AI learning digest from a YouTube archive. "
        "Cut intros, outros, sponsor chatter, repetition, hype, and low-value transitions. "
        "Keep durable concepts, procedures, definitions, examples, and caveats. "
        "Return only JSON with keys title, chapters, and changes_summary. "
        "The title must be a short no-fluff learning title, not a YouTube headline."
    )
    user_prompt = (
        "Build the digest from these source chapters. Each output chapter must include: "
        "source_indices, concept, summary, content, timestamp_start, timestamp_end, image_policy. "
        "image_policy must be minimal, keep, or drop. Use minimal for most chapters.\n\n"
        f"{json.dumps(source_payload, ensure_ascii=False)}"
    )

    if selected_model.startswith("openai:"):
        raw = _call_openai_agent(selected_model, system_prompt, user_prompt)
    elif selected_model.startswith("anthropic:"):
        raw = _call_anthropic_agent(selected_model, system_prompt, user_prompt)
    else:
        raise RuntimeError(f"Unsupported digest agent model: {selected_model}")

    parsed = _extract_json_object(raw)
    chapters = parsed.get("chapters", [])
    if not isinstance(chapters, list):
        raise RuntimeError("Digest agent returned invalid chapters")

    digest_chapters = []
    for chapter in chapters:
        normalized = _normalize_agent_chapter(source_dir, source_chapters, chapter)
        if normalized:
            digest_chapters.append(normalized)

    changes = parsed.get("changes_summary", [])
    if not isinstance(changes, list):
        changes = []
    changes = [str(item) for item in changes[:12]]
    if not changes:
        changes = ["Removed filler sections and reduced image context to verified minimal visuals."]

    title = str(parsed.get("title") or "")
    return digest_chapters, changes, title


def _call_openai_agent(selected_model: str, system_prompt: str, user_prompt: str) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")

    from openai import OpenAI

    model = os.environ.get("OPENAI_DIGEST_MODEL", selected_model.split(":", 1)[1])
    client = OpenAI(api_key=api_key)
    response = client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        max_tokens=6000,
    )
    return response.choices[0].message.content or ""


def _call_anthropic_agent(selected_model: str, system_prompt: str, user_prompt: str) -> str:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not configured")

    model = os.environ.get("ANTHROPIC_DIGEST_MODEL", selected_model.split(":", 1)[1])
    body = json.dumps({
        "model": model,
        "max_tokens": 6000,
        "temperature": 0.2,
        "system": system_prompt,
        "messages": [{"role": "user", "content": user_prompt}],
    }).encode("utf-8")
    request = urllib.request.Request(
        "https://api.anthropic.com/v1/messages",
        data=body,
        method="POST",
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Anthropic digest request failed: {detail}") from exc

    content = payload.get("content", [])
    text_parts = [part.get("text", "") for part in content if part.get("type") == "text"]
    return "\n".join(text_parts)


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
    return json.loads(cleaned[start:end])


def _normalize_agent_chapter(
    source_dir: Path,
    source_chapters: list[dict[str, Any]],
    chapter: dict[str, Any],
) -> dict[str, Any] | None:
    indices = chapter.get("source_indices", [])
    if not isinstance(indices, list):
        indices = []
    valid_indices = [idx for idx in indices if isinstance(idx, int) and 0 <= idx < len(source_chapters)]
    if not valid_indices:
        valid_indices = [_nearest_chapter_index(source_chapters, chapter.get("timestamp_start", 0))]

    source_group = [source_chapters[idx] for idx in valid_indices]
    content = _compact_content(str(chapter.get("content") or " ".join(str(c.get("content", "")) for c in source_group)))
    if not content:
        return None

    start = _to_float(chapter.get("timestamp_start"), source_group[0].get("timestamp_start", 0))
    end = _to_float(chapter.get("timestamp_end"), source_group[-1].get("timestamp_end", start + 60))
    image_policy = str(chapter.get("image_policy", "minimal")).lower()
    max_images = 0 if image_policy == "drop" else (2 if image_policy == "keep" else 1)
    images, review = _select_verified_images(source_dir, source_group, max_images=max_images)

    return {
        "concept": str(chapter.get("concept") or source_group[0].get("concept") or "AI Digest Chapter"),
        "summary": str(chapter.get("summary") or source_group[0].get("summary") or "")[:500],
        "content": content,
        "timestamp_start": start,
        "timestamp_end": max(end, start),
        "images": images,
        "source_indices": valid_indices,
        "image_review": review,
    }


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

        images, review = _select_verified_images(source_dir, [chapter], max_images=1)
        digest.append({
            "concept": chapter.get("concept") or "AI Digest Chapter",
            "summary": chapter.get("summary") or "",
            "content": content,
            "timestamp_start": _to_float(chapter.get("timestamp_start"), 0),
            "timestamp_end": _to_float(chapter.get("timestamp_end"), chapter.get("timestamp_start", 0)),
            "images": images,
            "source_indices": [index],
            "image_review": review,
        })

    if not digest and keep_at_least_one and source_chapters:
        return _generate_deterministic_digest(source_dir, source_chapters[:1], keep_at_least_one=True)

    changes = [
        f"Removed {removed} low-value or filler chapter(s).",
        "Compacted chapter text for agent learning context.",
        "Reduced visual context to verified minimal images.",
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


def _select_verified_images(
    source_dir: Path,
    source_chapters: list[dict[str, Any]],
    max_images: int,
) -> tuple[list[str], dict[str, Any]]:
    candidates: list[str] = []
    for chapter in source_chapters:
        for image in chapter.get("images", []) or []:
            if image not in candidates:
                candidates.append(image)

    scored = []
    rejected = []
    for image in candidates:
        score, reason = _score_image(source_dir, image)
        if score > 0:
            scored.append((score, image))
        else:
            rejected.append({"image": image, "reason": reason})

    scored.sort(reverse=True)
    kept = [image for _, image in scored[:max_images]]
    review = {
        "considered": len(candidates),
        "kept": len(kept),
        "rejected": rejected[:8],
    }
    return kept, review


def _score_image(source_dir: Path, relative_path: str) -> tuple[float, str]:
    if not relative_path or Path(relative_path).is_absolute():
        return 0, "invalid path"

    image_path = (source_dir / relative_path).resolve()
    if not image_path.is_relative_to(source_dir) or not image_path.exists():
        return 0, "missing image"

    try:
        with Image.open(image_path) as image:
            width, height = image.size
            if width < 120 or height < 90:
                return 0, "too small"

            gray = image.convert("L")
            gray.thumbnail((180, 180))
            stat = ImageStat.Stat(gray)
            mean = stat.mean[0]
            contrast = stat.stddev[0]
            histogram = gray.histogram()
            total = sum(histogram) or 1
            dark_ratio = sum(histogram[:18]) / total
            light_ratio = sum(histogram[238:]) / total

            if dark_ratio > 0.92:
                return 0, "mostly black"
            if light_ratio > 0.94:
                return 0, "mostly white"
            if contrast < 8:
                return 0, "low contrast"

            score = contrast + abs(mean - 128) * 0.05 - dark_ratio * 10
            return score, "kept"
    except Exception:
        return 0, "unreadable image"


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
