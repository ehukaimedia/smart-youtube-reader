# Archive Image Curation Spec

## Context

AI-selected chapter images can include poor context frames such as overlays, unrelated graphics, or unclear screenshots. Users need a manual way to clean the chapter context without deleting source project files.

## Expected Behavior

On the reader page, each chapter image should provide controls to:

- Open the image in a larger, focused view without mutating the archive.
- Remove the image from that chapter's `archive.json` image list.
- Replace the image by opening the slicer near that chapter's timestamp while keeping the current image attached until replacement frames are successfully saved.

The backend must persist these edits in `archive.json` so refreshes, learning prompts, and project ZIP downloads use the curated image set.
Replacement saves must target the original chapter and image path so the backend atomically swaps only that image after the new frames are copied.
When multiple curated slice saves contribute images to one chapter, the archive must track all contributing slice ids in insertion order while keeping `_slice_id` pointed at the latest curated slice for the chapter-level remove action. Deleting one slice removes only that slice's images and restores the original image set only after no curated slice images remain.
The reader must resolve replacement start times from both source `frames.json` entries and slice `slices/<id>/slice.json` manifests, because curated replacement images are stored as slice frames rather than source frames.
The larger image view must work for the project summary image and every chapter image. It should be opened by clicking the image, keep body scrolling locked while open, close from the backdrop, Close button, or Escape key, and expose an "Open original" link for inspecting the raw served asset. Source-image timestamp, quality, replace, and remove controls must stay clickable over the thumbnail and must not be swallowed by the larger-view trigger.

## Non-Goals

- Do not delete frame files from disk when removing context images.
- Do not automatically re-score image relevance.
- Do not alter transcript text or chapter boundaries.
