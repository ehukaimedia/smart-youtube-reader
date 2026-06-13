---
name: smart-youtube-reader
description: Use when an agent needs to extract structured knowledge from a YouTube video — transcripts, visual frames, and semantic chapter archives — so the content can be reasoned over, referenced, or turned into a reusable skill.
---

# Smart YouTube Reader

## Overview

Smart YouTube Reader turns a YouTube URL into structured, agent-readable data: a transcript, a deduplicated frame gallery, and an AI-generated semantic archive. Agents consume this output to learn from tutorials, generate SKILL.md files, or answer questions about video content.

## What It Produces

| Artifact | Path | Purpose |
|---|---|---|
| `transcript.json` | `data/jobs/<slug>_<id>/transcript.json` | Full text with timestamps (`text`, `start`, `duration`) |
| `frames/` | `data/jobs/<slug>_<id>/frames/*.png` | Deduplicated visual frames at configurable intervals |
| `archive.json` | `data/jobs/<slug>_<id>/archive.json` | AI-generated chapters with summaries and frame references |
| `manifest.json` | `data/jobs/<slug>_<id>/manifest.json` | Job metadata: title, URL, chapter count, status |

## API

**Base URL:** `http://localhost:8001`

### Submit a video
```http
POST /jobs
Content-Type: application/json

{
  "video_url": "https://www.youtube.com/watch?v=<id>",
  "interval_sec": 10,
  "min_width": 640
}
```
Returns `{ "job_id": "<uuid>" }`.

### Poll status
```http
GET /jobs/<job_id>
```
Returns `{ "status": "processing|complete|failed", "current_step": "...", "title": "..." }`.

Poll until `status === "complete"`, then read from `data/jobs/`.

## Learning a Skill from a Video

Once a job is complete, locate the output directory and prompt:

> "Analyze `archive.json` in `[absolute path to job dir]`.
> 1. Read `content` fields for technical concepts.
> 2. Reference frame images in `frames/` for visual/UI context.
> 3. Write a `SKILL.md` that codifies this knowledge as a reusable agent skill."

## Exploring a Job Visually

Use the **`youtube-archive-playground`** skill to turn a completed job into an interactive browser-based explorer. The playground lets you browse chapters, view operator-curated frames, and generate focused agent prompts from selected sections — useful when you want to share the archive with a human or build targeted follow-up prompts.

Trigger it with: `"make a playground for job <id>"` or `"build an explorer for this archive"`.

## Pipeline Steps

1. **Download** — yt-dlp fetches video using Chrome cookies if `YDL_COOKIES_BROWSER=chrome` is set
2. **Transcript** — `youtube-transcript-api` v1.x fetch; falls back to yt-dlp VTT parsing
3. **Frames** — FFmpeg extracts frames at `interval_sec`; FrameManager deduplicates via perceptual hash
4. **Archive** — Ollama Gemma 4 (`gemma4:12b`) chunks the transcript into semantic chapters, then uses vision to select representative frames per chapter (deterministic frame scoring as fallback)
5. **Package** — manifest written; directory renamed to `<slug>_<short_id>`

## Environment

| Variable | Default | Effect |
|---|---|---|
| `YDL_COOKIES_BROWSER` | unset | Set to `chrome` or `firefox` for private/age-restricted videos |
| `SMART_READER_MODEL` | `gemma4:12b` | Override the default Ollama Gemma 4 archive model (must be a vision-capable tag) |
| `OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama server endpoint the backend calls for archive generation |

## Common Issues

| Symptom | Cause | Fix |
|---|---|---|
| `n challenge solving failed` | No JS runtime in PATH | Check `~/.volta/bin` or `~/.nvm` has node |
| `Skipping client since it does not support cookies` | ios/android clients used with `cookiesfrombrowser` | Use `web` client (default) |
| `AttributeError: get_transcript` | `youtube-transcript-api` v0.x installed | Requires `>=1.0.0` |
| `Only images available` | n-challenge unsolved + no cookie-compatible client | Fix PATH so node is discoverable |
| Job stuck at processing | Ollama not running, or `gemma4:12b` not pulled | Start Ollama and run `ollama pull gemma4:12b`; the launch scripts also pull it if missing |
