import imagehash
from PIL import Image
from pathlib import Path
import ollama
import logging
import json

logger = logging.getLogger(__name__)

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

def align_frames_with_model(transcript: list, frames_dir: Path, model: str = "gemini-3-flash-preview") -> dict:
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
            # Call Ollama
            response = ollama.chat(model=model, messages=[
                {
                    'role': 'user',
                    'content': f"Does this image verify or illustrate the text: \"{chunk['text']}\"? Answer only YES or NO.",
                    'images': [str(best_frame)]
                }
            ])
            
            answer = response['message']['content'].strip().upper()
            logger.info(f"Checking frame {best_frame.name} against text '{chunk['text'][:20]}...': {answer}")
            
            if "YES" in answer:
                # Add to alignment at the end of the chunk
                alignment[chunk['start_index']] = best_frame.name
                
        except Exception as e:
            logger.error(f"Ollama inference failed: {e}")
            
    return alignment

def check_ollama_model(model_name: str = "gemini-3-flash-preview") -> bool:
    try:
        models = ollama.list()
        # ollama.list() returns a dict with 'models' key which is a list of dicts
        model_names = [m.get('name') for m in models.get('models', [])]
        
        if model_name in model_names or f"{model_name}:latest" in model_names:
            return True
        return False
    except Exception as e:
        logger.error(f"Failed to connect to Ollama: {e}")
        return False

def create_ai_archive(job_id: str, transcript: list, frame_manager, model: str = "gemini-3-flash-preview") -> dict:
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
            
        chunk_text = " ".join([t['text'] for t in chunk_items if 'text' in t])
        
        logger.info(f"Processing chunk: {current_time}s to {chunk_end}s (Length: {len(chunk_text)} chars)")
        
        try:
            # Prompt for semantic chunking of this segment
            system_prompt = (
                "You are an expert AI Data Archivist. Your goal is to convert the following video transcript segment "
                "into a structured dataset for machine learning. \n"
                "Action: Break the content into logical 'Concepts' or 'Chapters'. \n"
                "Output Format: JSON list of objects, each with: \n"
                " - 'title': Short concept title \n"
                " - 'summary': One sentence summary \n"
                " - 'content': The full text content for this section \n"
                " - 'start_time': approximate start time in seconds (relative to video start) \n"
                " - 'end_time': approximate end time in seconds \n"
                "IMPORTANT: Focus ONLY on the provided text. Do not hallucinate content outside this segment.\n"
                "CRITICAL: Output ONLY raw JSON. Do not wrap the JSON in markdown formatting or code blocks."
            )
            
            response = ollama.chat(model=model, messages=[
                {'role': 'system', 'content': system_prompt},
                {'role': 'user', 'content': f"Transcript Segment ({current_time}-{chunk_end}s): {chunk_text}"} 
            ])
            
            # Parse JSON output
            content = response['message']['content'].strip()

            # Clean up markdown if present
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            # Find JSON in content
            try:
                start = content.find('[')
                end = content.rfind(']') + 1
                if start == -1 or end == 0:
                    start = content.find('{')
                    end = content.rfind('}') + 1
                    json_str = "[" + content[start:end] + "]" if start != -1 and end != 0 else content
                else:
                    json_str = content[start:end]
                
                chunk_chapters = json.loads(json_str)
                all_chapters.extend(chunk_chapters)
                
            except Exception as e:
                logger.error(f"Failed to parse LLM JSON for chunk {current_time}: {e}. Content: {content[:100]}...")
                
        except Exception as e:
            logger.error(f"Ollama inference failed for chunk {current_time}: {e}")
            
        current_time += CHUNK_DURATION

    # Use the accumulated chapters
    chapters = all_chapters

    # 2. Select Images for each Chapter
    archive_data = []

    for chapter in chapters:
        c_start = chapter.get('start_time', 0)
        c_end = chapter.get('end_time', c_start + 60)
        
        # Get frame candidates from FrameManager (already sorted by time)
        # Note: we need to handle the frame_manager type hint if we want strictness, 
        # but for now we duck-type it.
        candidates = frame_manager.get_context_frames(c_start, c_end)
        
        selected_images = []
        if candidates:
            # Use Ollama to verify if the frame illustrates the chapter text
            
            # Reduce candidate size for efficiency if massive
            step = max(1, len(candidates) // 10)
            subset = candidates[::step]
            
            chapter_text = chapter.get('content', '')

            for frame_info in subset:
                if len(selected_images) >= 4:
                    break
                    
                filename = frame_info['filename']
                frame_path = frame_manager.frames_dir / filename
                
                try:
                    response = ollama.chat(model=model, messages=[
                        {
                            'role': 'user',
                            'content': f"Does this image verify or illustrate the text: \"{chapter_text[:200]}\"? Answer only YES or NO.",
                            'images': [str(frame_path)]
                        }
                    ])
                    
                    answer = response['message']['content'].strip().upper()

                    if "YES" in answer:
                        selected_images.append(filename)
                except Exception as e:
                    logger.error(f"Ollama inference failed during image selection: {e}")

        # Fallback if logic selected nothing (should trigger at least one if candidates exist)
        if not selected_images and candidates:
            selected_images.append(candidates[len(candidates)//2]['filename'])

        archive_data.append({
            "concept": chapter.get('title'),
            "summary": chapter.get('summary'),
            "content": chapter.get('content'),
            "timestamp_start": c_start,
            "timestamp_end": c_end,
            "images": selected_images
        })
        
    return {"job_id": job_id, "archive": archive_data}
