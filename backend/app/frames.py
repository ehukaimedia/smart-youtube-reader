import json
import logging
import imagehash
from PIL import Image
from pathlib import Path
from typing import List, Dict, Optional, Set

logger = logging.getLogger(__name__)

class FrameManager:
    """
    Manages video frames, handling efficient hashing, deduplication, and persistence.
    """
    def __init__(self, job_dir: Path):
        self.job_dir = job_dir
        self.frames_dir = job_dir / "frames"
        self.metadata_path = job_dir / "frames.json"
        
        # Data structure:
        # {
        #   "my_frame.png": {
        #       "phash": "hash_string",
        #       "timestamp": 12.5  (derived from filename or passed in)
        #   }
        # }
        self.frames: Dict[str, dict] = {} 
        self._load()

    def _load(self):
        """Load existing metadata if available."""
        if self.metadata_path.exists():
            try:
                with open(self.metadata_path, 'r') as f:
                    self.frames = json.load(f)
            except Exception as e:
                logger.error(f"Failed to load frames.json: {e}")
                self.frames = {}

    def save(self):
        """Persist metadata to disk."""
        try:
            with open(self.metadata_path, 'w') as f:
                json.dump(self.frames, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save frames.json: {e}")

    def scan_and_hash(self, interval_sec: float = 1.0) -> int:
        """
        Scans frames_dir, calculates PHash for new files, and removes orphan entries.
        Returns the number of new frames hashed.
        """
        if not self.frames_dir.exists():
            logger.warning(f"Frames directory not found: {self.frames_dir}")
            return 0

        # List current files
        # pattern: 0001.png, 0002.png etc.
        disk_files = sorted(list(self.frames_dir.glob("*.png")))
        disk_filenames = {f.name: f for f in disk_files}
        
        # 1. Clean up orphans (entries in json but not on disk)
        valid_keys = set(self.frames.keys()) & set(disk_filenames.keys())
        orphans = set(self.frames.keys()) - set(disk_filenames.keys())
        if orphans:
            logger.info(f"Removing {len(orphans)} orphan entries from metadata.")
            for o in orphans:
                del self.frames[o]

        # 2. Hash new files
        new_count = 0
        for name, path in disk_filenames.items():
            if name not in self.frames:
                try:
                    # Calculate Hash
                    with Image.open(path) as img:
                        # Convert to simple hex string for JSON storage
                        h = str(imagehash.phash(img))
                    
                    # Estimate timestamp
                    # ffmpeg output %04d.png usually 1-based.
                    # Frame 1 = 0s? or 1*frame_duration?
                    # Let's assume input frame number maps linearly to interval.
                    frames_num = int(path.stem) # '0001' -> 1
                    timestamp = (frames_num - 1) * interval_sec
                    
                    self.frames[name] = {
                        "phash": h,
                        "timestamp": timestamp,
                        "frame_idx": frames_num
                    }
                    new_count += 1
                except Exception as e:
                    logger.error(f"Error hashing {name}: {e}")

        if new_count > 0 or orphans:
            self.save()
            
        logger.info(f"FrameManager scanned. New hashes: {new_count}. Total cached: {len(self.frames)}")
        return new_count

    def deduplicate(self, threshold: int = 5) -> int:
        """
        Removes visually similar sequential frames based on cached PHash.
        Returns number of frames removed.
        """
        if not self.frames:
            return 0

        # Sort by frame index to ensure temporal processing
        sorted_frames = sorted(
            self.frames.items(), 
            key=lambda x: x[1]['frame_idx']
        )
        
        removed_count = 0
        last_kept_hash = None
        
        # Convert hex strings back to ImageHash objects for comparison
        def to_hash_obj(hex_str: str):
            return imagehash.hex_to_hash(hex_str)

        for name, data in sorted_frames:
            current_hash_obj = to_hash_obj(data['phash'])
            
            is_duplicate = False
            if last_kept_hash is not None:
                diff = current_hash_obj - last_kept_hash
                if diff < threshold:
                    is_duplicate = True
            
            if is_duplicate:
                # Remove from disk
                file_path = self.frames_dir / name
                try:
                    if file_path.exists():
                        file_path.unlink()
                    # Remove from metadata
                    del self.frames[name]
                    removed_count += 1
                except Exception as e:
                    logger.error(f"Failed to delete duplicate {name}: {e}")
            else:
                last_kept_hash = current_hash_obj

        if removed_count > 0:
            self.save()
            logger.info(f"Deduplication finished. Removed {removed_count} frames.")
            
        return removed_count

    def get_context_frames(self, start_time: float, end_time: float) -> List[dict]:
        """
        Returns all frames within a time window (inclusive).
        Returned list items contain {filename, timestamp, phash}.
        """
        found = []
        for name, data in self.frames.items():
            ts = data['timestamp']
            if start_time <= ts <= end_time:
                found.append({
                    "filename": name,
                    "timestamp": ts,
                    "phash": data['phash'],
                    "frame_idx": data['frame_idx']
                })
        
        # Sort by time
        found.sort(key=lambda x: x['timestamp'])
        return found
