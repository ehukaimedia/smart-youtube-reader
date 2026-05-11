import json
import logging
import imagehash
from PIL import Image, ImageFilter, ImageStat
from pathlib import Path
from typing import List, Dict

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

    def _measure_visual_signal(self, image: Image.Image) -> dict:
        """
        Return cheap frame-quality signals used by archive image selection.
        Values are normalized to 0..1 so downstream scoring can stay model-free.
        """
        sample = image.convert("RGB")
        sample.thumbnail((160, 90))
        gray = sample.convert("L")

        gray_values = list(gray.getdata())
        total = max(len(gray_values), 1)
        stat = ImageStat.Stat(gray)
        brightness = stat.mean[0] / 255.0
        contrast = stat.stddev[0] / 128.0
        dark_ratio = sum(1 for value in gray_values if value < 24) / total
        light_ratio = sum(1 for value in gray_values if value > 235) / total

        edge_image = gray.filter(ImageFilter.FIND_EDGES)
        edge_stat = ImageStat.Stat(edge_image)
        edge_density = edge_stat.mean[0] / 255.0

        rgb_stat = ImageStat.Stat(sample)
        rgb_pixels = list(sample.getdata())
        skin_pixels = 0
        for red, green, blue in rgb_pixels:
            if (
                red > 95
                and green > 40
                and blue > 20
                and red > green
                and red > blue
                and max(red, green, blue) - min(red, green, blue) > 15
                and abs(red - green) > 15
            ):
                skin_pixels += 1
        skin_ratio = skin_pixels / max(len(rgb_pixels), 1)

        channel_spread = (
            abs(rgb_stat.mean[0] - rgb_stat.mean[1])
            + abs(rgb_stat.mean[1] - rgb_stat.mean[2])
            + abs(rgb_stat.mean[0] - rgb_stat.mean[2])
        ) / (3 * 255.0)

        visual_score = (
            min(contrast, 1.0) * 0.36
            + min(edge_density * 3.0, 1.0) * 0.34
            + min(channel_spread * 4.0, 1.0) * 0.18
            + (1.0 - abs(brightness - 0.48) * 2.0) * 0.12
        )
        if dark_ratio > 0.72:
            visual_score *= 0.45
        if light_ratio > 0.82:
            visual_score *= 0.55
        if contrast < 0.08 and edge_density < 0.025:
            visual_score *= 0.35
        if skin_ratio > 0.22 and edge_density < 0.045:
            visual_score *= 0.72

        return {
            "brightness": round(max(0.0, min(brightness, 1.0)), 4),
            "contrast": round(max(0.0, min(contrast, 1.0)), 4),
            "edge_density": round(max(0.0, min(edge_density, 1.0)), 4),
            "color_spread": round(max(0.0, min(channel_spread, 1.0)), 4),
            "dark_ratio": round(max(0.0, min(dark_ratio, 1.0)), 4),
            "light_ratio": round(max(0.0, min(light_ratio, 1.0)), 4),
            "skin_ratio": round(max(0.0, min(skin_ratio, 1.0)), 4),
            "visual_score": round(max(0.0, min(visual_score, 1.0)), 4),
        }

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
        orphans = set(self.frames.keys()) - set(disk_filenames.keys())
        if orphans:
            logger.info(f"Removing {len(orphans)} orphan entries from metadata.")
            for o in orphans:
                del self.frames[o]

        # 2. Hash new files and backfill quality metadata for older caches.
        new_count = 0
        updated_count = 0
        for name, path in disk_filenames.items():
            if name not in self.frames or "visual_score" not in self.frames[name]:
                try:
                    # Calculate Hash
                    with Image.open(path) as img:
                        # Convert to simple hex string for JSON storage
                        h = self.frames.get(name, {}).get("phash") or str(imagehash.phash(img))
                        visual_stats = self._measure_visual_signal(img)
                    
                    # Estimate timestamp
                    # ffmpeg output %04d.png usually 1-based.
                    # Frame 1 = 0s? or 1*frame_duration?
                    # Let's assume input frame number maps linearly to interval.
                    frames_num = int(path.stem) # '0001' -> 1
                    timestamp = (frames_num - 1) * interval_sec
                    
                    was_new = name not in self.frames
                    existing = self.frames.get(name, {})
                    self.frames[name] = {
                        **existing,
                        "phash": h,
                        "timestamp": existing.get("timestamp", timestamp),
                        "frame_idx": existing.get("frame_idx", frames_num),
                        **visual_stats,
                    }
                    if was_new:
                        new_count += 1
                    else:
                        updated_count += 1
                except Exception as e:
                    logger.error(f"Error hashing {name}: {e}")

        if new_count > 0 or updated_count > 0 or orphans:
            self.save()
            
        logger.info(
            f"FrameManager scanned. New hashes: {new_count}. "
            f"Quality updates: {updated_count}. Total cached: {len(self.frames)}"
        )
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
                frame = {
                    "filename": name,
                    "timestamp": ts,
                    "phash": data['phash'],
                    "frame_idx": data['frame_idx']
                }
                for key in (
                    "brightness",
                    "contrast",
                    "edge_density",
                    "color_spread",
                    "dark_ratio",
                    "light_ratio",
                    "skin_ratio",
                    "visual_score",
                ):
                    if key in data:
                        frame[key] = data[key]
                found.append(frame)
        
        # Sort by time
        found.sort(key=lambda x: x['timestamp'])
        return found
