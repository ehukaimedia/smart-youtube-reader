# Smart YouTube Reader

**Smart YouTube Reader** is an official Ehukai Media open-source project. It turns any YouTube URL into a structured, AI-readable archive — transcript, de-duplicated visual frames, and semantic chapters — that you or an AI agent can search, read, and learn from.

> **Why this exists:** Videos are great for watching, but terrible for referencing. This tool makes video content as accessible and searchable as a book.

---

## Architecture & Design

### Local-First Design
Smart YouTube Reader is built on a **local-first** architecture.
* **No Database**: It uses the local filesystem for all storage. Jobs, transcripts, and frames are kept under the `data/` directory.
* **Privacy & Control**: All processing is performed on your machine.
* **Backend**: A FastAPI (Python) server handles the orchestration, yt-dlp downloading, FFmpeg frame slicing, image de-duplication (using image hashes), and local MLX-VLM server management.
* **Frontend**: A Next.js (React) application provides a visual dashboard, an interactive reader with timestamp-linked transcript search, and a clip-slicer.

### Local AI Model Expectations
For semantic chaptering and visual summary generation, Smart YouTube Reader uses Apple's **MLX-VLM** framework to execute models locally.
* **Hardware Requirement**: Running the local AI model requires **Apple Silicon macOS** (M1/M2/M3/M4 chipsets). This is because the underlying `mlx` library is optimized exclusively for Apple Silicon GPU acceleration.
* **Default Model**: The application defaults to `mlx-community/gemma-4-e4b-it-4bit`, a highly optimized quantized visual model from the Gemma 4 family.
* **Non-Apple Silicon Systems**: On Linux or Intel-based Windows/macOS, the app's downloader, transcript extraction, and frontend UI will function, but local AI model execution (archive chaptering) is not supported.

---

## What it produces

| File | What's inside |
|---|---|
| `transcript.json` | Full text with timestamps |
| `frames/` | De-duplicated screenshots at regular intervals |
| `archive.json` | AI-generated chapters, each with a summary and frame images |
| `manifest.json` | Job metadata (title, URL, chapter count) |

---

## Features

- **Semantic chapters** — AI reads the transcript and groups it into logical sections with titles and summaries
- **Visual matching** — Each chapter is paired with high-signal frames from the video using local frame metadata
- **Local model** — Archive generation uses Gemma 4 models through MLX-VLM
- **YouTube timestamp links** — Every chapter and transcript line links directly to that moment in the video
- **Video Slicer** — Cut precise clips from any job and export them with full metadata
- **Agent-ready** — The `archive.json` output is designed to be read by AI agents; image URLs are fully resolved
- **External-agent AI Digests** — Copy a CLI task for Codex, Claude, or another LLM to create a shorter learning-focused digest without modifying the source project
- **AI Digest with Images** — Recommended setup: Codex paired with GPT 2.0 image generation creates novel teaching images after inspecting the archive text and real frame evidence
- **Group AI Digests** — Combine multiple completed projects into a novel cross-video lesson with durable facts, theory, hypotheses, and generated teaching images

---

## Prerequisites

To run Smart YouTube Reader locally, you need the following:

- **macOS (Apple Silicon)** — Required for local model generation.
- **FFmpeg** — Used for frame extraction and video slicing (`brew install ffmpeg`).
- **Python 3.10+**
- **Node.js 20+** (pinned in [frontend/.nvmrc](frontend/.nvmrc))

---

## Quick Start

### One-click launch (Mac)
```bash
./start.command
```
This automatically starts both the backend and frontend.

### Manual setup

**1. Backend**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
# To run tests, also install development dependencies:
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8001
```

**2. Frontend**
```bash
cd frontend
npm install
npm run dev -- --port 3001
```

Then open `http://localhost:3001` in your browser.

---

## Verification & Testing

We maintain a rigorous test and linting suite to ensure codebase health.

### Backend Verification
Verify the backend using `pytest`:
```bash
cd backend
source .venv/bin/activate
python -m pytest
```

### Frontend Verification
Run frontend linting and build checks to ensure code quality:
```bash
cd frontend
# Run linter
npm run lint

# Build the Next.js production bundle
npm run build
```

---

## CLIs & Tooling

### AI Digest CLI
AI digest creation is handled by external agents through a local CLI. The app does not run a local digest model or deterministic fallback in the backend. In the Reader, use `Copy AI Digest CLI Task` or `Copy AI Digest with Images CLI Task` to copy the exact workflow for Codex, Claude, or another capable LLM.

The recommended image-rich workflow is Codex paired with GPT 2.0 image generation: Codex reads the archive text, inspects the source frame images as evidence, writes the digest draft, creates the novel teaching images, and then runs the materialization command. The CLI remains provider-agnostic; the requirement is that the agent actually inspect the project evidence before writing text or creating images.

```bash
python3 tools/create_ai_digest_version.py "data/jobs/<project-folder>"
```

For an image-rich digest task, add `--with-images`:

```bash
python3 tools/create_ai_digest_version.py "data/jobs/<project-folder>" --with-images
```

Both commands print the exact task for Codex, Claude, or another agent. The agent writes a JSON draft, then materializes the digest project:

```bash
python3 tools/create_ai_digest_version.py "data/jobs/<project-folder>" --draft "data/jobs/<project-folder>/generated/ai-digest-draft.json"
```

The CLI creates a separate `kind: ai_digest` project under `data/jobs/`; the original project is not modified. Plain AI digests preserve image references from kept source chapters so humans can curate images later. AI digests with images create one novel generated teaching image per digest chapter, up to six images total, and reference only safe `generated/` paths in the derived project.

Every digest task includes `preservation_items` extracted from the archive and transcript slices. Treat them as a checklist for names, metrics, benchmarks, examples, and claim direction so the digest is shorter without losing the facts that make the video useful.

### Group AI Digest CLI
Group digest creation combines two or more completed projects into one new learning project. From the Dashboard, select completed projects and use `Copy Group AI Digest CLI Task` to copy the external-agent workflow.

Unlike a single-video digest, a group digest is not a playlist export and does not preserve original frame paths. The agent reads every source `archive.json`, inspects frame images as evidence, and writes a novel combined transcript rather than concatenating source transcripts. Each chapter must teach digestible facts, theory, and a testable hypothesis, and the CLI rejects drafts that are too extractive from the source wording.

The materialized group project contains exactly three newly generated teaching images. Codex with GPT 2.0 image generation is the recommended pairing for this step because the images should be created from the new combined lesson plus the inspected visual evidence, not from prompt-only guesses.

```bash
python3 tools/create_group_ai_digest_version.py "data/jobs/<project-one>" "data/jobs/<project-two>" --title "Combined Learning Digest"
```

That prints the exact task for Codex, Claude, or another agent. The agent writes the group draft and creates the three image files in the printed staging folder, then runs the materialization command printed by the CLI. The result is a separate `kind: group_ai_digest` project under `data/jobs/` with a `Group AI Digest` dashboard badge. The source projects stay untouched.

### Summary Thumbnail CLI
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

---

## Agent Integration

The `archive.json` produced by each job is designed to be consumed by AI agents. Each archive includes timestamped chapter text plus local frame references, so external LLMs can reason from both transcript and visual evidence.

Digest workflows turn that archive into new agent-readable projects:

- **Single-project AI Digest** — Compresses one source video into a dense learning version while preserving important names, metrics, examples, and source frame references.
- **AI Digest with Images** — Uses an external LLM plus image generation to create novel teaching images under `generated/`; source frames are evidence, not output images.
- **Group AI Digest** — Synthesizes multiple projects into a new lesson with its own transcript, exactly three generated teaching images, and a `Group AI Digest` badge.

See [`skills/smart-youtube-reader/SKILL.md`](./skills/smart-youtube-reader/SKILL.md) for the full agent skill definition.

---

## Community & Governance

We welcome contributions and value our community's safety and security. Please review the following guidelines before participating:

* **[Contributing Guidelines](CONTRIBUTING.md)**: Learn how to set up your environment, follow project standards, and submit pull requests.
* **[Code of Conduct](CODE_OF_CONDUCT.md)**: Our expectations for community behavior and reporting enforcement.
* **[Security Policy](SECURITY.md)**: Instructions on how to privately report security vulnerabilities.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
