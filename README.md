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
- **Visual matching** — Each chapter is paired with the most relevant frames from the video
- **Model choice** — Use a local Ollama model (free, private) or a cloud NVIDIA NIM model (more powerful)
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
- At least one model pulled, e.g. `ollama pull gemma4`
- [FFmpeg](https://ffmpeg.org/) — `brew install ffmpeg`
- Node.js 18+ and Python 3.10+

## Using NVIDIA Cloud Models (optional)

If you have an [NVIDIA NIM API key](https://build.nvidia.com/), you can use powerful cloud models instead of (or alongside) local Ollama models.

1. Open `backend/.env`
2. Replace the placeholder with your key:
   ```
   NVIDIA_API_KEY=nvapi-your-key-here
   ```
3. Restart the backend

The model dropdown on the home page will then show both local and cloud options, including free-tier models like `minimax/minimax-m2.7`.

> **Tip:** Vision-capable models (e.g. `nvidia/llama-3.2-11b-vision-instruct`) do AI-verified image matching. Text-only models still generate chapters but use timestamp-based image selection instead.

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | Next.js (React) — `http://localhost:3001` |
| Backend | FastAPI (Python) — `http://localhost:8001` |
| Local AI | Ollama |
| Cloud AI | NVIDIA NIM (OpenAI-compatible) |
| Video | yt-dlp + FFmpeg |
| Storage | Local filesystem (no database) |

## Agent Integration

The `archive.json` produced by each job is designed to be consumed by AI agents. See [`skills/smart-youtube-reader/SKILL.md`](./skills/smart-youtube-reader/SKILL.md) for the full agent skill definition.

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
