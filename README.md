# Smart YouTube Reader

**Smart YouTube Reader** turns any YouTube URL into a structured, AI-readable archive — transcript, de-duplicated visual frames, and semantic chapters — that you or an AI agent can search, read, and learn from.

> **Why this exists:** Videos are great for watching, but terrible for referencing. This tool makes video content as accessible and searchable as a book.

## What it produces

| File | What's inside |
|---|---|
| `transcript.json` | Full text with timestamps |
| `frames/` | De-duplicated screenshots at regular intervals |
| `archive.json` | AI-generated chapters, each with a summary and frame images |
| `manifest.json` | Job metadata (title, URL, chapter count) |

## Features

- **Semantic chapters** — AI reads the transcript and groups it into logical sections with titles and summaries
- **Visual matching** — Each chapter is paired with high-signal frames from the video using local frame metadata
- **Local model** — Archive generation uses `smart-reader:latest`, built from the Gemma4-based Modelfile
- **YouTube timestamp links** — Every chapter and transcript line links directly to that moment in the video
- **Video Slicer** — Cut precise clips from any job and export them with full metadata
- **Agent-ready** — The `archive.json` output is designed to be read by AI agents; image URLs are fully resolved

## Quick Start

### One-click launch (Mac)
```bash
./start.command
```
This starts both the backend and frontend automatically.

### Manual setup

**Backend**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

**Frontend**
```bash
cd frontend
npm install
npm run dev -- --port 3001
```

Then open `http://localhost:3001`.

## Prerequisites

- [Ollama](https://ollama.com/) installed and running (`ollama serve`)
- `smart-reader:latest` built from `backend/modelfiles/smart-reader.Modelfile`
- [FFmpeg](https://ffmpeg.org/) — `brew install ffmpeg`
- Node.js 18+ and Python 3.10+

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (React) — `http://localhost:3001` |
| Backend | FastAPI (Python) — `http://localhost:8001` |
| Local AI | Ollama (`smart-reader:latest`) |
| Video | yt-dlp + FFmpeg |
| Storage | Local filesystem (no database) |

## Agent Integration

The `archive.json` produced by each job is designed to be consumed by AI agents. See [`skills/smart-youtube-reader/SKILL.md`](./skills/smart-youtube-reader/SKILL.md) for the full agent skill definition.

## AI Digest CLI

AI digest creation is handled by external agents through a local CLI. The app does not run a local digest model or deterministic fallback in the backend.

```bash
python3 tools/create_ai_digest_version.py "data/jobs/<project-folder>"
```

That prints the exact task for Codex, Claude, or another agent. The agent writes a JSON draft, then materializes the digest project:

```bash
python3 tools/create_ai_digest_version.py "data/jobs/<project-folder>" --draft "data/jobs/<project-folder>/generated/ai-digest-draft.json"
```

The CLI creates a separate `kind: ai_digest` project under `data/jobs/`. It preserves image references from kept source chapters; image removal and replacement stay in the human curation workflow.

## Group AI Digest CLI

Group digest creation combines two or more completed projects into one new learning project. Unlike a single-video digest, a group digest does not preserve original frame paths. Source frames are evidence only. The materialized group project contains a novel transcript and exactly three newly generated teaching images. Each chapter must teach digestible facts, theory, and a testable hypothesis, and the CLI rejects drafts that are too extractive from the source wording.

```bash
python3 tools/create_group_ai_digest_version.py "data/jobs/<project-one>" "data/jobs/<project-two>" --title "Combined Learning Digest"
```

That prints the exact task for Codex, Claude, or another agent. The agent writes the group draft and creates the three image files in the printed staging folder, then runs the materialization command printed by the CLI. The result is a separate `kind: group_ai_digest` project under `data/jobs/` with a `Group AI Digest` dashboard badge.

## Summary Thumbnail CLI

Create a project thumbnail from the archive text and attached frame images:

```bash
python3 tools/create_summary_thumbnail.py "data/jobs/<project-folder>"
```

You can also pass a job id:

```bash
python3 tools/create_summary_thumbnail.py "a24af63e-96e3-4ca5-9f59-5f04707889e4"
```

The tool writes `generated/summary.png` inside the project and updates both `archive.json` and `manifest.json` with:

```json
"summary_image": "generated/summary.png"
```

The dashboard uses that image as the project thumbnail.

## License

MIT
