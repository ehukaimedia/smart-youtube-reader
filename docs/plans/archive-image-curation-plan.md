# Archive Image Curation Plan

## Steps

1. Add a backend endpoint to remove a chapter image reference from `archive.json`.
2. Add per-image Remove and Replace controls to the reader archive preview.
3. Make Replace remove the current context image and open the slicer with the chapter timestamp preloaded.
4. Make the slicer return to the reader after saving a replacement slice to the project.
5. Verify changes persist through `archive.json` and survive page refresh.
6. Wrap summary and chapter images in an accessible larger-view trigger while keeping source-image QA controls clickable.
7. Add a reader lightbox that locks page scroll, closes from backdrop, Close, or Escape, and links to the original served image.
