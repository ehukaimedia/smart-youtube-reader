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

def _format_transcript_chunk(chunk_items: list, max_chars: int = MAX_PROMPT_CHARS) -> str:
    """
    Give the model compact timestamped evidence instead of one undifferentiated blob.
    This improves boundary selection while keeping the prompt bounded.
    """
    lines = []
    for item in chunk_items:
        start = _to_float(item.get("start"), 0.0)
        duration = _to_float(item.get("duration"), 0.0)
        end = start + duration
        text = _clean_transcript_text(item.get("text", ""))
        if text:
            lines.append(f"[{start:.1f}-{end:.1f}] {text}")

    rendered = "\n".join(lines)
    if len(rendered) <= max_chars:
        return rendered

    # Preserve the beginning and end of long windows so chapter boundaries stay grounded.
    head_budget = max_chars // 2
    tail_budget = max_chars - head_budget - 120
    return (
        rendered[:head_budget].rstrip()
        + "\n[...middle transcript omitted for context budget...]\n"
        + rendered[-tail_budget:].lstrip()
    )

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

def create_ai_archive(job_id: str, transcript: list, frame_manager, model: str = "smart-reader:latest") -> dict:
    """
    Creates a perfect AI-readable archive.
    1. Semantic Chunking: Groups transcript into concepts.
    2. Image Selection: Picks the best frame for each concept.
    """
    logger.info("Creating AI Archive...")
    
    # 1. Chunking Logic (Process in 5-minute segments to avoid context limits)
    CHUNK_DURATION = 300  # 5 minutes in seconds
    
    # Sort transcript just in case
    transcript.sort(key=lambda x: x.get('start', 0))
    
    video_duration = transcript[-1]['start'] + transcript[-1]['duration'] if transcript else 0
    all_chapters = []
    
    current_time = 0
    while current_time < video_duration:
        chunk_end = current_time + CHUNK_DURATION
        
        # Filter transcript for this window
        chunk_items = [
            t for t in transcript 
            if t['start'] >= current_time and t['start'] < chunk_end
        ]
        
        if not chunk_items:
            current_time += CHUNK_DURATION
            continue
            
        chunk_text = _format_transcript_chunk(chunk_items)
        
        logger.info(f"Processing chunk: {current_time}s to {chunk_end}s (Length: {len(chunk_text)} chars)")
        
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
                {'role': 'user', 'content': f"Transcript segment {current_time:.1f}-{chunk_end:.1f}s:\n{chunk_text}"}
            ]).strip()

            try:
                chunk_chapters = _extract_json_list(content)
                all_chapters.extend(chunk_chapters)
                
            except Exception as e:
                logger.error(f"Failed to parse LLM JSON for chunk {current_time}: {e}. Content: {content[:100]}...")
                
        except Exception as e:
            logger.error(f"LLM inference failed for chunk {current_time}: {e}")
            
        current_time += CHUNK_DURATION

    # Use the accumulated chapters
    chapters = all_chapters

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
        
    return {"job_id": job_id, "archive": archive_data}
