import imagehash
from PIL import Image
from pathlib import Path
import ollama
import logging
import json
import re

logger = logging.getLogger(__name__)
MAX_PROMPT_CHARS = 14000
MAX_IMAGES_PER_CHAPTER = 2
CHUNK_DURATION = 300

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
    resp = ollama.chat(model=model, messages=messages)
    return resp['message']['content']

def _clean_transcript_text(text: str) -> str:
    return re.sub(r"\s+", " ", text or "").strip()

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

def align_frames_with_model(transcript: list, frames_dir: Path, model: str = "smart-reader:latest") -> dict:
    """
     aligns images to transcript segments.
     Returns a dict: { transcript_index: image_filename }
    """
    logger.info("Starting intelligent alignment...")
    
    # Get all available frames (sorted)
    frame_files = sorted(list(frames_dir.glob("*.png")))
    if not frame_files:
        return {}
        
    # Build a timestamp-to-frame map for quick lookup
    # filenames are 0001.png etc, effectively 1-based index of 15s intervals
    # OR we can assume filename implies time if we named them differently.
    # Current pipeline names them %04d.png based on sequence. 
    # Logic: frame N = N * interval_sec (approx). 
    # Better: use the file modification time or just assume the interval from the request.
    # Limitation: We don't have the interval here easily unless we pass it or check metadata.
    # Let's assume we pass a rough map or just use the frames we have.
    
    # Simplified approach: 
    # 1. Divide transcript into chunks (e.g. every 10 lines or by gap).
    # 2. For each chunk, find the frame that falls in its time range.
    # 3. Query Ollama: "Does this image illustrate the following text: '{text}'? Answer YES or NO."
    # 4. If YES, keep it.
    
    alignment = {}
    
    # Group transcript into chunks for context
    chunks = []
    current_chunk = []
    chunk_start_idx = 0
    
    for i, item in enumerate(transcript):
        current_chunk.append(item)
        # Break chunk on simple heuristics (e.g. full stop or length)
        text = item['text']
        if text.strip().endswith(('.', '?', '!')) or len(current_chunk) > 5:
            start_time = current_chunk[0]['start']
            end_time = current_chunk[-1]['start'] + current_chunk[-1]['duration']
            chunks.append({
                'text': " ".join([t['text'] for t in current_chunk]),
                'start': start_time,
                'end': end_time,
                'start_index': chunk_start_idx
            })
            current_chunk = []
            chunk_start_idx = i + 1
            
    # Process chunks of text with relevant frames
    # We'll assume frames are at 15s intervals. 0001.png = 0s? No, ffmpeg starts at 0.
    # 0001.png is likely the first frame.
    # We need to know the interval. For now, let's just find *any* frame in the window.
    
    # Hack: Inspect one frame to see if we can get metadata? 
    # Or just assume 15s for now as it's the default.
    INTERVAL = 15 
    
    for chunk in chunks:
        # Find frames in this time window
        candidates = []
        for i, f in enumerate(frame_files):
            # timestamp approx
            t = (i + 1) * INTERVAL # 1-based index from ffmpeg loop usually?
            # Actually ffmpeg '%04d.png' generates 0001, 0002...
            # If we started at 0, 0001 is 0s? 
            # Let's assume frame i (0-based list) corresponds to time i * INTERVAL.
            time_approx = i * INTERVAL
            
            if chunk['start'] - INTERVAL <= time_approx <= chunk['end'] + INTERVAL:
                candidates.append(f)
                
        if not candidates:
            continue
            
        # Pick the middle candidate to test
        best_frame = candidates[len(candidates)//2]
        
        try:
            answer = _chat(model, [
                {
                    'role': 'user',
                    'content': f"Does this image verify or illustrate the text: \"{chunk['text']}\"? Answer only YES or NO.",
                    'images': [str(best_frame)]
                }
            ]).strip().upper()
            logger.info(f"Checking frame {best_frame.name} against text '{chunk['text'][:20]}...': {answer}")
            
            if "YES" in answer:
                # Add to alignment at the end of the chunk
                alignment[chunk['start_index']] = best_frame.name
                
        except Exception as e:
            logger.error(f"LLM inference failed: {e}")
            
    return alignment

def check_ollama_model(model_name: str = "smart-reader:latest") -> bool:
    try:
        result = ollama.list()
        model_names = [m.model for m in result.models if m.model]
        return model_name in model_names or f"{model_name}:latest" in model_names
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        return False

def create_ai_archive(
    job_id: str,
    transcript: list,
    frame_manager,
    model: str = "smart-reader:latest",
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
            # Prompt for semantic chunking of this segment
            system_prompt = (
                "You are a Smart YouTube Reader archive planner. Convert timestamped transcript evidence into "
                "compact AI-learning chapters.\n"
                "Return ONLY a raw JSON array. No markdown, no prose.\n"
                "Each object must contain exactly: title, summary, content, start_time, end_time.\n"
                "Use numeric seconds for timestamps. Derive them from the bracketed transcript ranges.\n"
                "Create 3-5 chapters for a 5-minute segment when the segment contains enough substance. Merge tiny transitions into nearby chapters.\n"
                "Do not create standalone chapters for intros, sponsor chatter, calls to action, jokes, or repetition.\n"
                "Preserve durable concepts, definitions, procedures, examples, caveats, and references to visible charts, slides, or tools.\n"
                "The content field must use transcript wording from the provided segment, ordered chronologically. "
                "Keep the teaching evidence dense; target 400-900 characters per chapter when possible. "
                "Do not invent facts or add outside knowledge.\n"
                "Keep titles no-fluff: specific lesson names, no hype, no YouTube-style phrasing."
            )
            
            content = _chat(model, [
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"Transcript segment {chunk['start']:.1f}-{chunk['end']:.1f}s:\n{chunk_text}"}
            ]).strip()

            try:
                chunk_chapters = _extract_json_list(content)
                all_chapters.extend(chunk_chapters)
                transcript_integrity["chunks_succeeded"] += 1
                
            except Exception as e:
                logger.error(f"Failed to parse LLM JSON for chunk {chunk['start']}: {e}. Content: {content[:100]}...")
                transcript_integrity["chunks_failed"] += 1
                transcript_integrity["chunk_errors"].append({
                    "chunk": chunk_index,
                    "start": chunk["start"],
                    "end": chunk["end"],
                    "error": str(e),
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
    chapters = all_chapters
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
        selected_images = _choose_representative_frames(
            candidates,
            all_frames,
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
        })
        
    return {"job_id": job_id, "archive": archive_data, "transcript_integrity": transcript_integrity}
