# Smart YouTube Reader (Gemini 3.0 Edition)

**Smart YouTube Reader** is a local, AI-powered "Knowledge Engine" that transforms YouTube videos into structured, searchable libraries. By combining **Gemini 3 Flash Preview** (via Ollama) with advanced computer vision, it extracts the *complete* narrative of a video—text, context, and visual keyframes—into a format you can actually use.

> **Why this exists:** Videos are great for watching, but terrible for referencing. This tool makes video content as accessible and searchable as a book.

![App Screenshot](/frontend/public/screenshot.png)

## 🧠 Core Intelligence

*   **Model:** Powered by `gemini-3-flash-preview:latest` (Ollama) for ultra-fast, long-context understanding.
*   **Vision:** Uses Perceptual Hashing (ImageHash) and SSIM to de-duplicate frames and find the "perfect" visual match for every paragraph of text.
*   **Local Privacy:** All processing happens on your machine. No API keys required.

## ✨ Key Features

### 1. The Smart Reader
Reads like a Medium article, watches like a video.
*   **Aligned Visuals:** Text paragraphs are automatically paired with the exact frame from the video.
*   **Active Reading:** Click any paragraph to jump the video to that exact timestamp.

### 2. Semantic AI Archive
Organize chaos into structure.
*   **Auto-Chaptering:** AI breaks the video into logical sections with descriptive titles.
*   **Visual Summaries:** Each chapter gets a generated gallery of key visuals.

### 3. Precision Video Slicer
Extract the gold.
*   **Frame-Perfect Cuts:** Select start/end points with millisecond precision.
*   **Clean Data:** Slices are saved with full metadata, ready for re-use in creative workflows (like *Smart Image Animations*).
*   **Integrity Check:** Review every frame in a filmstrip view to ensure no blurry or transition frames make the cut.

## 🤖 Agent Integration

This tool is built to feed data into Antigravity Agents.
*   **Learn from Video:** Turn a 20-minute coding tutorial into a `SKILL.md` for your agent.
*   **Read the Guide:** [Agent Integration Guide](./AGENT_INTEGRATION.md)


## 🛠️ Tech Stack & Ports

*   **Frontend:** Next.js 16.1 (React 19) - `http://localhost:3001`
*   **Backend:** FastAPI (Python 3.10+) - `http://localhost:8001`
*   **Database:** Local JSON/Filesystem (Zero-config).

## 🚀 Quick Start

### Option A: The "One-Click" Script (Recommended)
We provide a unified launcher that handles environments and dependencies.

```bash
# MacOS / Linux
./start.command
# (Automatically launches http://localhost:3001)
```

### Option B: Manual Setup

**1. Backward (API)**
```bash
cd backend
python3 -m venv .venv        # Create standard venv
source .venv/bin/activate    # Activate
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8001
```

**2. Frontend (UI)**
```bash
cd frontend
npm install
npm run dev -- --port 3001
```

## 📦 Prerequisites

*   [Ollama](https://ollama.com/) installed and running.
    *   **Pull the model:** `ollama pull gemini-3-flash-preview`
*   [FFmpeg](https://ffmpeg.org/) installed (`brew install ffmpeg`).
*   Node.js 18+ and Python 3.10+.

## License

MIT
