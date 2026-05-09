# Dashboard YouTube Thumbnails Spec

## Context

Project cards on the dashboard only showed text metadata, which made completed video jobs harder to scan.

## Expected Behavior

Each dashboard project card should show a YouTube thumbnail derived from the job's `video_url`.

Supported URL forms:

- `https://www.youtube.com/watch?v=<id>`
- `https://youtu.be/<id>`
- `https://www.youtube.com/shorts/<id>`
- `https://www.youtube.com/embed/<id>`

If a usable video ID cannot be parsed, the card should keep a stable thumbnail area and show a neutral fallback instead of shifting layout.

## Non-Goals

- Do not download or store thumbnails in the backend.
- Do not change the job API response shape.
- Do not block the dashboard if a public YouTube thumbnail fails to load.
