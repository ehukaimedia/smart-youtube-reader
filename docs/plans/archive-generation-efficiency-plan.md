# Archive Generation Efficiency Plan

## Steps

1. Remove NVIDIA/NIM model exposure from the backend model list.
2. Simplify archive chat routing to local MLX.
3. Expose supported MLX Gemma 4 archive models.
4. Update archive prompt instructions for compact no-fluff learning chapters.
5. Format transcript chunks with timestamp ranges before sending them to the model.
6. Store per-frame visual quality signals during frame indexing.
7. Rank initial chapter images by visual signal, timestamp proximity, and duplicate distance.
8. Persist selected-image context metadata so the reader can show timestamps and quality scores.
9. Add reader controls that let operators improve chapter images directly from the chapter.
10. Update architecture playground and README so the documented flow matches the MLX implementation.
11. Verify backend modules compile and the model endpoint no longer returns API-backed models.
