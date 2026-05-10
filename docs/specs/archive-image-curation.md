# Archive Image Curation Spec

## Context

AI-selected chapter images can include poor context frames such as overlays, unrelated graphics, or unclear screenshots. Users need a manual way to clean the chapter context without deleting source project files.

## Expected Behavior

On the reader page, each chapter image should provide controls to:

- Remove the image from that chapter's `archive.json` image list.
- Replace the image by opening the slicer near that chapter's timestamp while keeping the current image attached until replacement frames are successfully saved.

The backend must persist these edits in `archive.json` so refreshes, learning prompts, and project ZIP downloads use the curated image set.
Replacement saves must target the original chapter and image path so the backend atomically swaps only that image after the new frames are copied.

## Non-Goals

- Do not delete frame files from disk when removing context images.
- Do not automatically re-score image relevance.
- Do not alter transcript text or chapter boundaries.
