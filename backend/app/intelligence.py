import imagehash
from PIL import Image
from pathlib import Path
import base64
import io
import logging
import json
import re
from html import unescape
from .model_runtime import DEFAULT_MODEL, chat as model_chat, check_model

logger = logging.getLogger(__name__)
MAX_PROMPT_CHARS = 14000
MAX_IMAGES_PER_CHAPTER = 2
VISION_FRAME_CANDIDATES = 6
VISION_IMAGE_MAX_SIDE = 768
CHUNK_DURATION = 300
ARCHIVE_RESPONSE_FORMAT = "xml"
ARCHIVE_XML_ATTEMPTS = 2
MIN_CHAPTER_DURATION = 3.0
MIN_GAP_CHAPTER_DURATION = 12.0
MIN_GAP_MEANINGFUL_WORDS = 30
_CAPTION_NOISE_RE = re.compile(r"(?:>>\s*)?\[(?:music|applause|laughter|noise|sound|silence|inaudible)[^\]]*\](?:\s*>>)?", re.IGNORECASE)
_SENTENCE_END_RE = re.compile(r"[.!?]")
EVIDENCE_STOPWORDS = {
    "about", "after", "again", "alone", "also", "another", "because", "before",
    "being", "between", "could", "every", "from", "have", "into", "itself",
    "just", "like", "more", "much", "only", "other", "over", "same", "some",
    "than", "that", "their", "them", "then", "there", "these", "they", "this",
    "through", "what", "when", "where", "which", "while", "with", "without",
    "would", "your",
}

def _to_float(value, default: float) -> float:
    try:
        return float(value) if value is not None else default
    except (TypeError, ValueError):
        return default

def _chat(model: str, messages: list) -> str:
    """
    Local Ollama chat call.
    Returns the response content string.
    """
    return model_chat(model=model, messages=messages)

def _clean_transcript_text(text: str) -> str:
    stripped = _CAPTION_NOISE_RE.sub(" ", text or "")
    return re.sub(r"\s+", " ", stripped).strip()


def _trim_to_sentence_boundary(text: str, min_keep_ratio: float = 0.5) -> str:
    if not text or text[-1] in ".!?":
        return text
    match = None
    for m in _SENTENCE_END_RE.finditer(text):
        match = m
    if match is None:
        return text
    cut = match.end()
    if cut < len(text) * min_keep_ratio:
        return text
    return text[:cut].rstrip()


def _evidence_tokens(text: str) -> list[str]:
    tokens = re.findall(r"[a-z0-9]+", (text or "").lower())
    return [
        token
        for token in tokens
        if token not in EVIDENCE_STOPWORDS and (len(token) >= 4 or token.isdigit())
    ]


def _meaningful_word_count(text: str) -> int:
    return len(_evidence_tokens(text))


def _item_start_end(item: dict) -> tuple[float, float]:
    start = _to_float(item.get("start"), 0.0)
    return start, start + _to_float(item.get("duration"), 0.0)


def _transcript_items_in_range(transcript: list[dict], start: float, end: float) -> list[dict]:
    return [
        item
        for item in transcript
        if start <= _to_float(item.get("start"), 0.0) < end
    ]


def _chapter_evidence_text(chapter: dict) -> str:
    return " ".join([
        str(chapter.get("title") or chapter.get("concept") or ""),
        str(chapter.get("summary") or ""),
        str(chapter.get("content") or ""),
    ])


def _row_matches_chapter_evidence(row_text: str, chapter_text: str) -> bool:
    row_tokens = _evidence_tokens(row_text)
    if not row_tokens:
        return False
    chapter_tokens = _evidence_tokens(chapter_text)
    if not chapter_tokens:
        return False

    chapter_ngrams = set()
    for size in (5, 4):
        if len(row_tokens) < size:
            continue
        chapter_ngrams.update(
            tuple(chapter_tokens[index:index + size])
            for index in range(0, len(chapter_tokens) - size + 1)
        )
        if any(
            tuple(row_tokens[index:index + size]) in chapter_ngrams
            for index in range(0, len(row_tokens) - size + 1)
        ):
            return True

    return False


def _matching_transcript_evidence_items(
    transcript: list[dict],
    chapter_text: str,
    max_window_items: int = 5,
) -> list[dict]:
    matched_indexes = set()
    for start_index in range(len(transcript)):
        for size in range(1, max_window_items + 1):
            window = transcript[start_index:start_index + size]
            if not window:
                continue
            window_text = " ".join(str(item.get("text") or "") for item in window)
            if _row_matches_chapter_evidence(window_text, chapter_text):
                matched_indexes.update(range(start_index, start_index + len(window)))
    return [item for index, item in enumerate(transcript) if index in matched_indexes]


def _expand_chapters_to_transcript_evidence(
    chapters: list[dict],
    transcript: list[dict],
    boundary_start: float,
    boundary_end: float,
) -> tuple[list[dict], list[dict]]:
    expanded = []
    repairs = []
    relevant_transcript = _transcript_items_in_range(transcript, boundary_start, boundary_end)

    for index, chapter in enumerate(chapters):
        chapter_text = _chapter_evidence_text(chapter)
        matched = _matching_transcript_evidence_items(relevant_transcript, chapter_text)
        updated = dict(chapter)
        if matched:
            evidence_start = min(_item_start_end(item)[0] for item in matched)
            evidence_end = max(_item_start_end(item)[1] for item in matched)
            start = max(boundary_start, min(updated["start_time"], evidence_start))
            end = min(boundary_end, max(updated["end_time"], evidence_end))
            if start != updated["start_time"] or end != updated["end_time"]:
                repairs.append({
                    "chapter": index,
                    "action": "expanded_to_cover_transcript_evidence",
                    "from": [updated["start_time"], updated["end_time"]],
                    "to": [start, end],
                })
                updated["start_time"] = start
                updated["end_time"] = end
        expanded.append(updated)

    return expanded, repairs


def _fallback_chapter_title(text: str) -> str:
    lowered = text.lower()
    if "production agent" in lowered and "architectural choices" in lowered:
        return "Production Agent Architecture Choices"
    if "full harness itself" in lowered or "explicit and executable" in lowered:
        return "Explicit Executable Harness Logic"
    if "terminal bench" in lowered and "accuracy" in lowered:
        return "Meta-Harness Benchmark Results"
    if "transfer" in lowered and "harness" in lowered:
        return "Transferability of Optimized Harnesses"
    if "prompt injection" in lowered or "vulnerab" in lowered:
        return "Harness Security Risks"
    if "model" in lowered and "harness" in lowered:
        return "Additional Model and Harness Evidence"
    tokens = _evidence_tokens(text)[:6]
    return " ".join(token.capitalize() for token in tokens) or "Additional Transcript Evidence"


def _clip_text(text: str, max_chars: int = 900) -> str:
    cleaned = _clean_transcript_text(text)
    if len(cleaned) <= max_chars:
        return cleaned
    clipped = cleaned[:max_chars].rsplit(" ", 1)[0].strip()
    return clipped + "."


def _fallback_gap_summary(text: str) -> str:
    first_sentence = re.split(r"(?<=[.!?])\s+", _clean_transcript_text(text), maxsplit=1)[0]
    return _clip_text(first_sentence, max_chars=220)


def _add_transcript_gap_chapters(
    chapters: list[dict],
    transcript: list[dict],
    boundary_start: float,
    boundary_end: float,
) -> tuple[list[dict], list[dict]]:
    if not transcript:
        return chapters, []

    repaired = sorted([dict(chapter) for chapter in chapters], key=lambda item: item["start_time"])
    additions = []
    repairs = []

    cursor = boundary_start
    for chapter in repaired + [{"start_time": boundary_end, "end_time": boundary_end}]:
        gap_start = cursor
        gap_end = chapter["start_time"]
        if gap_end - gap_start >= MIN_GAP_CHAPTER_DURATION:
            gap_items = _transcript_items_in_range(transcript, gap_start, gap_end)
            gap_text = _clean_transcript_text(" ".join(str(item.get("text") or "") for item in gap_items))
            if _meaningful_word_count(gap_text) >= MIN_GAP_MEANINGFUL_WORDS:
                fallback = {
                    "title": _fallback_chapter_title(gap_text),
                    "summary": _fallback_gap_summary(gap_text),
                    "content": _trim_to_sentence_boundary(_clip_text(gap_text)),
                    "start_time": gap_start,
                    "end_time": gap_end,
                    "_fallback": "transcript_gap",
                }
                additions.append(fallback)
                repairs.append({
                    "action": "added_transcript_gap_chapter",
                    "start": gap_start,
                    "end": gap_end,
                    "title": fallback["title"],
                })
        cursor = max(cursor, chapter["end_time"])

    if not additions:
        return repaired, repairs

    return sorted(repaired + additions, key=lambda item: (item["start_time"], item["end_time"])), repairs

def _transcript_line(item: dict) -> str:
    start = _to_float(item.get("start"), 0.0)
    duration = _to_float(item.get("duration"), 0.0)
    end = start + duration
    text = _clean_transcript_text(item.get("text", ""))
    return f"[{start:.1f}-{end:.1f}] {text}" if text else ""

def _format_transcript_chunk(chunk_items: list, max_chars: int | None = MAX_PROMPT_CHARS) -> str:
    """
    Give the model compact timestamped evidence instead of one undifferentiated blob.
    This function never drops middle transcript content; callers that need a
    bounded prompt must split first with _transcript_prompt_chunks().
    """
    lines = [line for item in chunk_items if (line := _transcript_line(item))]
    rendered = "\n".join(lines)
    return rendered


def _transcript_prompt_chunks(
    transcript: list,
    chunk_duration: int = CHUNK_DURATION,
    max_chars: int = MAX_PROMPT_CHARS,
) -> list[dict]:
    """
    Split transcript into complete prompt chunks without truncating transcript rows.
    A long time window is split into smaller adjacent chunks instead of omitting
    its middle text.
    """
    if not transcript:
        return []

    ordered = [
        {**item, "_source_index": index}
        for index, item in enumerate(sorted(transcript, key=lambda item: _to_float(item.get("start"), 0.0)))
    ]
    max_start = max(_to_float(item.get("start"), 0.0) for item in ordered)
    video_duration = max(
        _to_float(item.get("start"), 0.0) + _to_float(item.get("duration"), 0.0)
        for item in ordered
    )
    prompt_chunks: list[dict] = []
    current_time = 0.0

    while current_time <= max_start:
        chunk_end = min(current_time + chunk_duration, video_duration)
        is_final_window = chunk_end >= video_duration
        window_items = [
            item for item in ordered
            if (
                current_time <= _to_float(item.get("start"), 0.0) < chunk_end
                or (is_final_window and _to_float(item.get("start"), 0.0) == chunk_end)
            )
        ]
        current_group: list[dict] = []
        current_chars = 0

        for item in window_items:
            for prompt_item in _split_prompt_item(item, max_chars):
                line_len = len(_transcript_line(prompt_item)) + 1
                if current_group and current_chars + line_len > max_chars:
                    prompt_chunks.append(_prompt_chunk_payload(current_group))
                    current_group = []
                    current_chars = 0
                current_group.append(prompt_item)
                current_chars += line_len

        if current_group:
            prompt_chunks.append(_prompt_chunk_payload(current_group))

        current_time += chunk_duration
        if current_time >= video_duration:
            break

    emitted = {
        item.get("_source_index")
        for chunk in prompt_chunks
        for item in chunk["items"]
        if item.get("_source_index") is not None
    }
    if len(emitted) != len(ordered):
        missing = sorted(set(range(len(ordered))) - emitted)
        raise RuntimeError(
            f"Transcript prompt chunking lost {len(ordered) - len(emitted)} source row(s): {missing[:10]}"
        )

    return prompt_chunks


def _split_prompt_item(item: dict, max_chars: int) -> list[dict]:
    line = _transcript_line(item)
    if len(line) <= max_chars:
        return [item]

    start = _to_float(item.get("start"), 0.0)
    duration = _to_float(item.get("duration"), 0.0)
    prefix = f"[{start:.1f}-{start + duration:.1f}] "
    text = _clean_transcript_text(item.get("text", ""))
    budget = max(max_chars - len(prefix), 80)
    parts = _split_text_by_budget(text, budget)
    logger.warning(
        "Transcript row at %.1fs exceeded prompt budget and was split into %s pieces.",
        start,
        len(parts),
    )
    return [{**item, "text": part} for part in parts]


def _split_text_by_budget(text: str, budget: int) -> list[str]:
    words = text.split()
    parts: list[str] = []
    current: list[str] = []
    current_len = 0

    for word in words:
        if len(word) > budget:
            if current:
                parts.append(" ".join(current))
                current = []
                current_len = 0
            parts.extend(word[index:index + budget] for index in range(0, len(word), budget))
            continue

        next_len = current_len + len(word) + (1 if current else 0)
        if current and next_len > budget:
            parts.append(" ".join(current))
            current = [word]
            current_len = len(word)
        else:
            current.append(word)
            current_len = next_len

    if current:
        parts.append(" ".join(current))
    return parts or [text[:budget]]


def _prompt_chunk_payload(items: list[dict]) -> dict:
    start = min(_to_float(item.get("start"), 0.0) for item in items)
    end = max(_to_float(item.get("start"), 0.0) + _to_float(item.get("duration"), 0.0) for item in items)
    text = _format_transcript_chunk(items, max_chars=None)
    return {
        "start": start,
        "end": end,
        "items": items,
        "text": text,
        "chars": len(text),
    }

def _extract_json_list(content: str) -> list:
    cleaned = content.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

    start = cleaned.find("[")
    end = cleaned.rfind("]") + 1
    if start == -1 or end == 0:
        start = cleaned.find("{")
        end = cleaned.rfind("}") + 1
        if start == -1 or end == 0:
            raise ValueError("No JSON object or list found")
        cleaned = "[" + cleaned[start:end] + "]"
    else:
        cleaned = cleaned[start:end]

    parsed = json.loads(cleaned)
    return parsed if isinstance(parsed, list) else [parsed]


def _strip_cdata(value: str) -> str:
    cleaned = value.strip()
    if cleaned.startswith("<![CDATA[") and cleaned.endswith("]]>"):
        cleaned = cleaned[9:-3].strip()
    return unescape(cleaned)


def _extract_xml_chapters(content: str) -> list[dict]:
    cleaned = content.strip()
    if "```xml" in cleaned:
        cleaned = cleaned.split("```xml", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

    archive_match = re.search(r"<archive\b[^>]*>(.*?)</archive\s*>", cleaned, re.I | re.S)
    body = archive_match.group(1) if archive_match else cleaned
    chapter_blocks = re.findall(r"<chapter\b[^>]*>(.*?)</chapter\s*>", body, re.I | re.S)
    if not chapter_blocks:
        raise ValueError("No XML chapter elements found")

    chapters = []
    errors = []
    for block in chapter_blocks:
        try:
            chapter = {}
            for key in ("title", "summary", "content", "start_time", "end_time"):
                match = re.search(rf"<{key}\b[^>]*>(.*?)</{key}\s*>", block, re.I | re.S)
                if not match:
                    raise ValueError(f"Missing XML field: {key}")
                value = _strip_cdata(match.group(1))
                if key in {"start_time", "end_time"}:
                    try:
                        chapter[key] = float(value)
                    except ValueError as exc:
                        raise ValueError(f"Invalid numeric XML field {key}: {value}") from exc
                else:
                    chapter[key] = value
            chapters.append(chapter)
        except ValueError as exc:
            errors.append(str(exc))
            logger.warning("Skipping malformed XML chapter: %s", exc)
    if not chapters:
        details = f": {errors[:3]}" if errors else ""
        raise ValueError(f"No valid XML chapter elements found{details}")
    return chapters


def _extract_archive_chapters(content: str, response_format: str = ARCHIVE_RESPONSE_FORMAT) -> list[dict]:
    if response_format == "xml":
        return _extract_xml_chapters(content)
    if response_format == "json":
        return _extract_json_list(content)
    raise ValueError(f"Unsupported archive response format: {response_format}")


def _archive_system_prompt(response_format: str = ARCHIVE_RESPONSE_FORMAT) -> str:
    base = (
        "You are a Smart YouTube Reader archive planner. Convert timestamped transcript evidence into "
        "compact AI-learning chapters.\n"
        "Use numeric seconds for timestamps. Derive them from the bracketed transcript ranges.\n"
        "Chapter start_time and end_time must stay inside the provided transcript segment, be sorted ascending, "
        "and never overlap. Leave gaps when transcript material is low-value.\n"
        "Create 3-5 chapters for a 5-minute segment when the segment contains enough substance. Merge tiny transitions into nearby chapters.\n"
        "Do not create standalone chapters for intros, sponsor chatter, calls to action, jokes, or repetition.\n"
        "Preserve durable concepts, definitions, procedures, examples, caveats, and references to visible charts, slides, or tools.\n"
        "The content field must use transcript wording from the provided segment, ordered chronologically. "
        "Keep the teaching evidence dense; target 400-900 characters per chapter when possible. "
        "Do not invent facts or add outside knowledge.\n"
        "Keep titles no-fluff: specific lesson names, no hype, no YouTube-style phrasing.\n"
    )
    if response_format == "xml":
        return (
            base
            + "Return ONLY XML. No markdown, no prose.\n"
            + "Use exactly this structure:\n"
            + "<archive>\n"
            + "  <chapter>\n"
            + "    <title>Specific lesson name</title>\n"
            + "    <summary>One compact summary sentence.</summary>\n"
            + "    <content>Grounded transcript evidence in chronological order.</content>\n"
            + "    <start_time>0.0</start_time>\n"
            + "    <end_time>60.0</end_time>\n"
            + "  </chapter>\n"
            + "</archive>"
        )
    return (
        base
        + "Return ONLY a raw JSON array. No markdown, no prose.\n"
        + "Each object must contain exactly: title, summary, content, start_time, end_time."
    )


def _archive_user_prompt(chunk: dict, previous_error: str | None = None) -> str:
    prompt = f"Transcript segment {chunk['start']:.1f}-{chunk['end']:.1f}s:\n{chunk['text']}"
    if previous_error:
        prompt += (
            "\n\nYour previous response could not be parsed: "
            f"{previous_error}. Return the requested structure again with every chapter containing "
            "title, summary, content, start_time, and end_time."
        )
    return prompt


def _generate_archive_chunk(model: str, chunk: dict) -> tuple[list[dict], dict]:
    attempts = []

    for attempt in range(1, ARCHIVE_XML_ATTEMPTS + 1):
        raw = _chat(model, [
            {'role': 'system', 'content': _archive_system_prompt("xml")},
            {'role': 'user', 'content': _archive_user_prompt(
                chunk,
                attempts[-1]["error"] if attempts else None,
            )},
        ]).strip()
        try:
            chapters = _extract_archive_chapters(raw, "xml")
            return chapters, {"format": "xml", "attempts": attempt, "fallback": False}
        except Exception as exc:
            error = str(exc)
            logger.error(
                "Failed to parse LLM XML for chunk %.1f on attempt %s: %s. Content: %s...",
                chunk["start"],
                attempt,
                error,
                raw[:100],
            )
            attempts.append({"format": "xml", "attempt": attempt, "error": error})

    raw = _chat(model, [
        {'role': 'system', 'content': _archive_system_prompt("json")},
        {'role': 'user', 'content': _archive_user_prompt(chunk, attempts[-1]["error"] if attempts else None)},
    ]).strip()
    try:
        chapters = _extract_archive_chapters(raw, "json")
        return chapters, {"format": "json", "attempts": len(attempts) + 1, "fallback": True}
    except Exception as exc:
        error = str(exc)
        logger.error(
            "Failed to parse LLM JSON fallback for chunk %.1f: %s. Content: %s...",
            chunk["start"],
            error,
            raw[:100],
        )
        attempts.append({"format": "json", "attempt": 1, "error": error})
        raise ValueError(f"Archive chunk parse failed after retries: {attempts}") from exc


def _normalize_generated_chapters(
    chapters: list[dict],
    boundary_start: float,
    boundary_end: float,
) -> tuple[list[dict], list[dict]]:
    """
    Repair model timeline drift before frame selection.
    The LLM chooses semantic boundaries, but the backend owns validity: chapters
    must be complete, bounded to their transcript evidence, sorted, and non-overlapping.
    """
    if boundary_end <= boundary_start:
        boundary_end = boundary_start + MIN_CHAPTER_DURATION

    normalized: list[dict] = []
    repairs: list[dict] = []

    for index, chapter in enumerate(chapters):
        title = _clean_transcript_text(str(chapter.get("title") or chapter.get("concept") or ""))
        summary = _clean_transcript_text(str(chapter.get("summary") or ""))
        content = _clean_transcript_text(str(chapter.get("content") or ""))
        if not title or not summary or not content:
            repairs.append({"chapter": index, "action": "dropped_empty_required_field"})
            continue

        raw_start = _to_float(chapter.get("start_time", chapter.get("timestamp_start")), boundary_start)
        raw_end = _to_float(chapter.get("end_time", chapter.get("timestamp_end")), raw_start + MIN_CHAPTER_DURATION)
        start = raw_start
        end = raw_end

        if end < start:
            start, end = end, start
            repairs.append({"chapter": index, "action": "swapped_inverted_range"})

        clamped_start = min(max(start, boundary_start), boundary_end)
        clamped_end = min(max(end, boundary_start), boundary_end)
        if clamped_start != start or clamped_end != end:
            repairs.append({
                "chapter": index,
                "action": "clamped_to_transcript_bounds",
                "from": [start, end],
                "to": [clamped_start, clamped_end],
            })
        start, end = clamped_start, clamped_end

        if end <= start:
            end = min(boundary_end, start + MIN_CHAPTER_DURATION)
            if end <= start:
                repairs.append({"chapter": index, "action": "dropped_zero_duration"})
                continue
            repairs.append({"chapter": index, "action": "expanded_zero_duration", "to": [start, end]})

        normalized_chapter = {
            "title": title,
            "summary": summary,
            "content": content,
            "start_time": start,
            "end_time": end,
            "_source_chapter_index": index,
        }
        if chapter.get("_fallback"):
            normalized_chapter["_fallback"] = chapter.get("_fallback")
        normalized.append(normalized_chapter)

    normalized.sort(key=lambda item: (item["start_time"], item["end_time"]))
    repaired: list[dict] = []
    for chapter in normalized:
        start = chapter["start_time"]
        end = chapter["end_time"]
        if repaired:
            prev = repaired[-1]
            prev_start = prev["start_time"]
            prev_end = prev["end_time"]
            if start < prev_end:
                if start > prev_start + MIN_CHAPTER_DURATION:
                    repairs.append({
                        "chapter": chapter["_source_chapter_index"],
                        "action": "trimmed_previous_overlap",
                        "previous_from": [prev_start, prev_end],
                        "previous_to": [prev_start, start],
                    })
                    prev["end_time"] = start
                else:
                    repairs.append({
                        "chapter": chapter["_source_chapter_index"],
                        "action": "shifted_start_after_previous",
                        "from": [start, end],
                        "to": [prev_end, end],
                    })
                    start = prev_end

        if end <= start:
            repairs.append({
                "chapter": chapter["_source_chapter_index"],
                "action": "dropped_after_overlap_repair",
            })
            continue

        chapter["start_time"] = start
        chapter["end_time"] = end
        chapter.pop("_source_chapter_index", None)
        repaired.append(chapter)

    return repaired, repairs

def _hash_distance(a: str | None, b: str | None) -> int | None:
    if not a or not b:
        return None
    try:
        return imagehash.hex_to_hash(a) - imagehash.hex_to_hash(b)
    except Exception:
        return None

def _candidate_score(frame: dict, target_time: float, chapter_start: float, chapter_end: float) -> float:
    duration = max(chapter_end - chapter_start, 1.0)
    distance = abs(_to_float(frame.get("timestamp"), target_time) - target_time)
    time_score = max(0.0, 1.0 - distance / max(duration * 0.55, 1.0))
    visual_score = _to_float(frame.get("visual_score"), 0.35)
    edge_score = min(_to_float(frame.get("edge_density"), 0.0) * 4.0, 1.0)
    dark_ratio = _to_float(frame.get("dark_ratio"), 0.0)
    light_ratio = _to_float(frame.get("light_ratio"), 0.0)
    skin_ratio = _to_float(frame.get("skin_ratio"), 0.0)
    color_spread = _to_float(frame.get("color_spread"), 0.0)

    structured_screen_score = 0.0
    if skin_ratio < 0.08 and dark_ratio > 0.5 and edge_score > 0.07:
        structured_screen_score += 0.22
    if 0.015 <= color_spread <= 0.09:
        structured_screen_score += 0.08

    dark_penalty = 0.0
    if dark_ratio > 0.9 and edge_score < 0.18:
        dark_penalty = (dark_ratio - 0.9) * 1.4

    skin_penalty = 0.0
    if skin_ratio > 0.14:
        skin_penalty = (skin_ratio - 0.14) * 1.55

    light_penalty = max(0.0, light_ratio - 0.86) * 0.65
    flat_promo_penalty = 0.18 if color_spread < 0.01 and dark_ratio < 0.45 else 0.0
    return (
        visual_score * 0.42
        + edge_score * 0.2
        + time_score * 0.16
        + structured_screen_score
        - dark_penalty
        - light_penalty
        - skin_penalty
        - flat_promo_penalty
    )

def _choose_representative_frames(
    candidates: list[dict],
    all_frames: list[dict],
    chapter_start: float,
    chapter_end: float,
    used_frames: set[str],
    max_images: int = MAX_IMAGES_PER_CHAPTER,
) -> list[str]:
    """
    Select useful teaching frames without LLM vision calls.
    Quality comes from frames.json visual signals; timestamps keep selections local.
    """
    duration = max(chapter_end - chapter_start, 1.0)
    targets = [chapter_start + duration * 0.5]
    if duration >= 45:
        targets = [chapter_start + duration * 0.35, chapter_start + duration * 0.72]

    selected: list[dict] = []
    seen_names: set[str] = set()

    def pick_from(pool: list[dict], target: float, prefer_unused: bool) -> dict | None:
        ranked = []
        has_unused = any(frame.get("filename") and frame.get("filename") not in used_frames for frame in pool)
        for frame in pool:
            name = frame.get("filename")
            if not name or name in seen_names:
                continue
            if name in used_frames and (prefer_unused or has_unused):
                continue
            too_similar = False
            for item in selected:
                distance = _hash_distance(frame.get("phash"), item.get("phash"))
                if distance is not None and distance < 8:
                    too_similar = True
                    break
            if too_similar:
                continue
            ranked.append((_candidate_score(frame, target, chapter_start, chapter_end), frame))
        if not ranked:
            return None
        ranked.sort(key=lambda item: item[0], reverse=True)
        return ranked[0][1]

    strong_candidates = [
        frame for frame in candidates
        if not (
            _to_float(frame.get("contrast"), 0.0) < 0.08
            and _to_float(frame.get("edge_density"), 0.0) < 0.018
        )
        and _to_float(frame.get("skin_ratio"), 0.0) < 0.18
    ] or candidates
    if (
        strong_candidates
        and all(frame.get("filename") in used_frames for frame in strong_candidates)
        and any(frame.get("filename") not in used_frames for frame in candidates)
    ):
        strong_candidates = candidates

    for target in targets:
        if len(selected) >= max_images:
            break
        chosen = pick_from(strong_candidates, target, prefer_unused=True)
        if chosen is None:
            chosen = pick_from(strong_candidates, target, prefer_unused=False)
        if chosen is not None:
            selected.append(chosen)
            seen_names.add(chosen["filename"])

    if not selected and all_frames:
        chapter_mid = chapter_start + duration * 0.5
        fallback_pool = [
            frame for frame in all_frames
            if not (
                _to_float(frame.get("contrast"), 0.0) < 0.08
                and _to_float(frame.get("edge_density"), 0.0) < 0.018
            )
            and _to_float(frame.get("skin_ratio"), 0.0) < 0.18
        ] or all_frames
        chosen = pick_from(fallback_pool, chapter_mid, prefer_unused=True)
        if chosen is None:
            chosen = pick_from(fallback_pool, chapter_mid, prefer_unused=False)
        if chosen is not None:
            selected.append(chosen)

    for frame in selected:
        used_frames.add(frame["filename"])
    return [frame["filename"] for frame in selected]


def _vision_candidate_targets(chapter_start: float, chapter_end: float) -> list[float]:
    duration = max(chapter_end - chapter_start, 1.0)
    if duration >= 45:
        return [chapter_start + duration * 0.35, chapter_start + duration * 0.72]
    return [chapter_start + duration * 0.5]


def _vision_candidate_pool(
    candidates: list[dict],
    all_frames: list[dict],
    chapter_start: float,
    chapter_end: float,
    used_frames: set[str],
    max_candidates: int = VISION_FRAME_CANDIDATES,
) -> list[dict]:
    pool = candidates or all_frames
    if not pool:
        return []

    has_unused = any(frame.get("filename") and frame.get("filename") not in used_frames for frame in pool)
    targets = _vision_candidate_targets(chapter_start, chapter_end)
    ranked = []
    for frame in pool:
        name = frame.get("filename")
        if not name:
            continue
        if name in used_frames and has_unused:
            continue
        score = max(
            _candidate_score(frame, target, chapter_start, chapter_end)
            for target in targets
        )
        ranked.append((score, frame))

    ranked.sort(key=lambda item: item[0], reverse=True)
    selected: list[dict] = []
    for _, frame in ranked:
        too_similar = False
        for item in selected:
            distance = _hash_distance(frame.get("phash"), item.get("phash"))
            if distance is not None and distance < 8:
                too_similar = True
                break
        if too_similar:
            continue
        selected.append(frame)
        if len(selected) >= max_candidates:
            break
    return selected


def _frame_image_base64(frames_dir: Path, frame: dict) -> str | None:
    name = frame.get("filename")
    if not name or Path(name).name != name:
        return None
    path = (frames_dir / name).resolve()
    try:
        if not path.is_file() or frames_dir.resolve() not in path.parents:
            return None
        with Image.open(path) as image:
            image = image.convert("RGB")
            image.thumbnail((VISION_IMAGE_MAX_SIDE, VISION_IMAGE_MAX_SIDE))
            buffer = io.BytesIO()
            image.save(buffer, format="JPEG", quality=82, optimize=True)
        return base64.b64encode(buffer.getvalue()).decode("ascii")
    except Exception as exc:
        logger.warning("Could not prepare frame %s for vision selection: %s", name, exc)
        return None


def _vision_selection_prompt(chapter: dict, frames: list[dict], max_images: int) -> str:
    frame_lines = "\n".join(
        f"{index}. {frame['filename']} at {float(frame.get('timestamp', 0.0)):.1f}s"
        for index, frame in enumerate(frames, start=1)
    )
    return (
        "Select the best video frames for this Smart YouTube Reader chapter.\n"
        "Choose frames that visibly teach, evidence, or clarify the chapter. Prefer charts, slides, UI, objects, "
        "or visual states over generic talking-head frames. Avoid dark, blurry, duplicate, transition, intro, "
        "or low-information frames.\n\n"
        f"Chapter title: {chapter.get('title') or chapter.get('concept') or ''}\n"
        f"Summary: {chapter.get('summary') or ''}\n"
        f"Content evidence: {chapter.get('content') or ''}\n\n"
        "Images are attached in this exact order:\n"
        f"{frame_lines}\n\n"
        f"Return ONLY JSON in this shape: {{\"selected\": [\"filename.png\"]}}. "
        f"Select 1-{max_images} filenames from the list above. Do not include explanations."
    )


def _extract_vision_selected_filenames(raw: str, allowed: set[str], max_images: int) -> list[str]:
    cleaned = raw.strip()
    if "```json" in cleaned:
        cleaned = cleaned.split("```json", 1)[1].split("```", 1)[0].strip()
    elif "```" in cleaned:
        cleaned = cleaned.split("```", 1)[1].split("```", 1)[0].strip()

    parsed = json.loads(cleaned)
    if isinstance(parsed, dict):
        values = parsed.get("selected") or parsed.get("images") or parsed.get("filenames") or []
    else:
        values = parsed
    if not isinstance(values, list):
        raise ValueError("Vision response selected field is not a list")

    selected: list[str] = []
    for value in values:
        name = str(value)
        if name in allowed and name not in selected:
            selected.append(name)
        if len(selected) >= max_images:
            break
    if not selected:
        raise ValueError("Vision response did not select any allowed filenames")
    return selected


def _choose_vision_representative_frames(
    model: str,
    chapter: dict,
    candidates: list[dict],
    all_frames: list[dict],
    frames_dir: Path,
    chapter_start: float,
    chapter_end: float,
    used_frames: set[str],
    max_images: int = MAX_IMAGES_PER_CHAPTER,
) -> tuple[list[str], dict]:
    vision_pool = _vision_candidate_pool(
        candidates,
        all_frames,
        chapter_start,
        chapter_end,
        used_frames,
    )
    image_payloads = []
    image_frames = []
    for frame in vision_pool:
        image_payload = _frame_image_base64(frames_dir, frame)
        if image_payload:
            image_payloads.append(image_payload)
            image_frames.append(frame)

    if not image_frames:
        selected = _choose_representative_frames(candidates, all_frames, chapter_start, chapter_end, used_frames, max_images)
        return selected, {
            "method": "deterministic",
            "fallback_reason": "no_vision_candidate_images",
            "vision_candidates": 0,
        }

    allowed = {frame["filename"] for frame in image_frames}
    try:
        raw = _chat(model, [
            {"role": "user", "content": _vision_selection_prompt(chapter, image_frames, max_images), "images": image_payloads},
        ]).strip()
        selected = _extract_vision_selected_filenames(raw, allowed, max_images)
        for name in selected:
            used_frames.add(name)
        return selected, {
            "method": "ollama_vision",
            "vision_candidates": len(image_frames),
        }
    except Exception as exc:
        logger.warning("Vision frame selection failed; using deterministic selector: %s", exc)
        selected = _choose_representative_frames(candidates, all_frames, chapter_start, chapter_end, used_frames, max_images)
        return selected, {
            "method": "deterministic",
            "fallback_reason": str(exc),
            "vision_candidates": len(image_frames),
        }

def _image_context_for_frames(frames: list[dict]) -> dict:
    context = {}
    for frame in frames:
        filename = frame.get("filename")
        if not filename:
            continue
        context[filename] = {
            "timestamp": frame.get("timestamp"),
            "visual_score": frame.get("visual_score"),
            "edge_density": frame.get("edge_density"),
            "dark_ratio": frame.get("dark_ratio"),
            "skin_ratio": frame.get("skin_ratio"),
        }
    return context

def deduplicate_frames(frames_dir: Path, threshold: int = 5) -> int:
    """
    Scans all images in frames_dir, computes PHash, and removes duplicates.
    Returns the number of removed frames.
    """
    hashes = {}
    removed_count = 0
    
    # Sort files to process in time order
    files = sorted(list(frames_dir.glob("*.png")))
    
    for file_path in files:
        try:
            with Image.open(file_path) as img:
                h = imagehash.phash(img)
            
            is_duplicate = False
            for existing_h in hashes:
                if h - existing_h < threshold:
                    is_duplicate = True
                    break
            
            if is_duplicate:
                file_path.unlink()
                removed_count += 1
            else:
                hashes[h] = file_path
                
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
            
    return removed_count

def check_local_model(model_name: str = DEFAULT_MODEL) -> bool:
    try:
        return check_model(model_name)
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        return False

def create_ai_archive(
    job_id: str,
    transcript: list,
    frame_manager,
    model: str = DEFAULT_MODEL,
    progress_callback=None,
) -> dict:
    """
    Creates a perfect AI-readable archive.
    1. Semantic Chunking: Groups transcript into concepts.
    2. Image Selection: Picks the best frame for each concept.
    """
    logger.info("Creating AI Archive...")
    
    # Sort transcript just in case
    transcript.sort(key=lambda x: x.get('start', 0))
    all_chapters = []

    prompt_chunks = _transcript_prompt_chunks(transcript)
    chunk_source_indexes = [
        item.get("_source_index")
        for chunk in prompt_chunks
        for item in chunk["items"]
        if item.get("_source_index") is not None
    ]
    transcript_integrity = {
        "source_items": len(transcript),
        "chunk_items": len(set(chunk_source_indexes)),
        "prompt_items": len(chunk_source_indexes),
        "prompt_chunks": len(prompt_chunks),
        "chunks_succeeded": 0,
        "chunks_failed": 0,
        "chunk_errors": [],
        "source_start": _to_float(transcript[0].get("start"), 0.0) if transcript else 0.0,
        "source_end": (
            _to_float(transcript[-1].get("start"), 0.0)
            + _to_float(transcript[-1].get("duration"), 0.0)
            if transcript else 0.0
        ),
    }

    for chunk_index, chunk in enumerate(prompt_chunks, start=1):
        chunk_text = chunk["text"]
        if progress_callback:
            progress_callback(chunk_index, len(prompt_chunks))

        logger.info(
            f"Processing chunk: {chunk['start']}s to {chunk['end']}s "
            f"(Items: {len(chunk['items'])}, Length: {len(chunk_text)} chars)"
        )
        
        try:
            # Prompt for semantic chunking of this segment.
            chunk_chapters, generation_meta = _generate_archive_chunk(model, chunk)
            chunk_chapters, timeline_repairs = _normalize_generated_chapters(
                chunk_chapters,
                chunk["start"],
                chunk["end"],
            )
            if timeline_repairs:
                transcript_integrity.setdefault("timeline_repairs", []).append({
                    "chunk": chunk_index,
                    "start": chunk["start"],
                    "end": chunk["end"],
                    "repairs": timeline_repairs,
                })
            all_chapters.extend(chunk_chapters)
            transcript_integrity["chunks_succeeded"] += 1
            if generation_meta.get("fallback"):
                transcript_integrity.setdefault("chunk_fallbacks", []).append({
                    "chunk": chunk_index,
                    "start": chunk["start"],
                    "end": chunk["end"],
                    **generation_meta,
                })
                
        except Exception as e:
            logger.error(f"LLM inference failed for chunk {chunk['start']}: {e}")
            transcript_integrity["chunks_failed"] += 1
            transcript_integrity["chunk_errors"].append({
                "chunk": chunk_index,
                "start": chunk["start"],
                "end": chunk["end"],
                "error": str(e),
            })

    if transcript_integrity["chunk_items"] != transcript_integrity["source_items"]:
        raise RuntimeError(
            "Transcript integrity check failed: "
            f"{transcript_integrity['chunk_items']} of {transcript_integrity['source_items']} source rows reached prompts"
        )
    if transcript_integrity["chunks_failed"]:
        raise RuntimeError(
            "Archive generation failed for "
            f"{transcript_integrity['chunks_failed']} of {transcript_integrity['prompt_chunks']} transcript chunk(s): "
            f"{transcript_integrity['chunk_errors'][:3]}"
        )

    # Use the accumulated chapters
    chapters, timeline_repairs = _normalize_generated_chapters(
        all_chapters,
        transcript_integrity["source_start"],
        transcript_integrity["source_end"],
    )
    if timeline_repairs:
        transcript_integrity.setdefault("timeline_repairs", []).append({
            "scope": "global",
            "repairs": timeline_repairs,
        })
    chapters, evidence_repairs = _expand_chapters_to_transcript_evidence(
        chapters,
        transcript,
        transcript_integrity["source_start"],
        transcript_integrity["source_end"],
    )
    if evidence_repairs:
        transcript_integrity.setdefault("timeline_repairs", []).append({
            "scope": "content_evidence",
            "repairs": evidence_repairs,
        })
        chapters, timeline_repairs = _normalize_generated_chapters(
            chapters,
            transcript_integrity["source_start"],
            transcript_integrity["source_end"],
        )
        if timeline_repairs:
            transcript_integrity.setdefault("timeline_repairs", []).append({
                "scope": "post_evidence_global",
                "repairs": timeline_repairs,
            })

    chapters, gap_repairs = _add_transcript_gap_chapters(
        chapters,
        transcript,
        transcript_integrity["source_start"],
        transcript_integrity["source_end"],
    )
    if gap_repairs:
        transcript_integrity.setdefault("timeline_repairs", []).append({
            "scope": "transcript_gaps",
            "repairs": gap_repairs,
        })
        chapters, timeline_repairs = _normalize_generated_chapters(
            chapters,
            transcript_integrity["source_start"],
            transcript_integrity["source_end"],
        )
        if timeline_repairs:
            transcript_integrity.setdefault("timeline_repairs", []).append({
                "scope": "post_gap_global",
                "repairs": timeline_repairs,
            })

    transcript_integrity["raw_chapters"] = len(all_chapters)
    transcript_integrity["normalized_chapters"] = len(chapters)
    if not chapters and transcript:
        raise RuntimeError("Archive generation returned no chapters")

    # 2. Select Images for each Chapter
    archive_data = []
    used_frames: set = set()  # Track frames used across chapters to avoid duplicates

    # Build a flat sorted list of all frames for fallback nearest-frame lookup
    all_frames = frame_manager.get_context_frames(0, float('inf'))

    for chapter in chapters:
        c_start = _to_float(chapter.get('start_time'), 0.0)
        c_end = _to_float(chapter.get('end_time'), c_start + 60.0)

        candidates = frame_manager.get_context_frames(max(0, c_start - 20), c_end + 20)
        selected_images, image_selection = _choose_vision_representative_frames(
            model,
            chapter,
            candidates,
            all_frames,
            frame_manager.frames_dir,
            c_start,
            c_end,
            used_frames,
        )
        context_pool = [frame for frame in candidates if frame.get("filename") in selected_images]
        context_names = {frame.get("filename") for frame in context_pool}
        missing_context = set(selected_images) - context_names
        if missing_context:
            context_pool.extend(frame for frame in all_frames if frame.get("filename") in missing_context)

        archive_data.append({
            "concept": chapter.get('title'),
            "summary": chapter.get('summary'),
            "content": chapter.get('content'),
            "timestamp_start": c_start,
            "timestamp_end": c_end,
            "images": selected_images,
            "_image_context": _image_context_for_frames(context_pool),
            "_image_selection": image_selection,
            **({"_fallback": chapter.get("_fallback")} if chapter.get("_fallback") else {}),
        })
        
    return {"job_id": job_id, "archive": archive_data, "transcript_integrity": transcript_integrity}
