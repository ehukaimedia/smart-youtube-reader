# Smart YouTube Reader

**Smart YouTube Reader** is an AI-powered local application that transforms YouTube videos into structured, searchable narratives. It uses **Gemini 3 Flash** (via Ollama) and advanced computer vision to extract "perfect" frames and align them with the video transcript, creating a rich multi-modal reading experience.

Features include a **Video Slicer** for frame-perfect clip extraction and an **AI Archive** that organizes content into semantic chapters.

![Screenshot](/frontend/public/screenshot.png)

## Features

-   **Smart Reader**: Converts videos into a blog-post style narrative with relevant images aligned to text.
-   **AI Archive**: Semantic chunking of video content into "Chapters" with summaries and multi-image galleries.
-   **Video Slicer**:
    -   **Frame-Perfect Extraction**: Select exact start/end times and FPS (10-60).
    -   **Visual Scrubbing**: Syncs start/end times automatically as you scrub the video.
    -   **Filmstrip Review**: Inspect every generated frame, exclude blurry/irrelevant ones, and save only the best.
    -   **Project Integration**: Saved slices appear directly in the main Reader timeline, integrated chronologically with AI chapters.
-   **Local Intelligence**: Runs entirely locally using `Ollama` and `FFmpeg`.

## Prerequisites

-   **Python 3.10+**
-   **Node.js 18+**
-   **FFmpeg** (Must be in your system PATH)
-   **Ollama** (Running locally with `gemini-3-flash-preview` or compatible model)

## Installation

1.  **Clone the repository**:
    ```bash
    git clone https://github.com/ehukaimedia/smart-youtube-reader.git
    cd smart-youtube-reader
    ```

2.  **Start the Application**:
    We provide a helper script to start both Frontend and Backend:
    ```bash
    ./start.command  # macOS
    # OR
    ./start.sh       # Linux/Mac terminal
    ```

    *Alternatively, run manually:*

    **Backend (Port 8001)**
    ```bash
    cd backend
    pip install -r requirements.txt
    python -m app.main
    ```

    **Frontend (Port 3001)**
    ```bash
    cd frontend
    npm install
    npm run dev
    ```

## Usage

1.  Open [http://localhost:3001](http://localhost:3001).
2.  **Paste a YouTube URL** to begin a new "Job".
3.  Wait for the AI to process the video (transcription, frame extraction, alignment).
4.  **View the Reader**: Read the content with synchronized images.
5.  **Use the Video Slicer**:
    -   Click **"Open Slicer"** from the Reader page.
    -   Select a clip range (e.g., "The explosion animation").
    -   Click **"Preview"** to see all frames.
    -   Deselect bad frames and click **"Add to Project"**.
    -   Return to the Reader to see your slice integrated into the story!

## Tech Stack

-   **Frontend**: Next.js 14, React, CSS Modules (Glassmorphism UI).
-   **Backend**: FastAPI, FFmpeg (pyffmpeg), SQLite (optional), Pydantic.
-   **AI/ML**: Ollama (LLM), ImageHash (Perceptual Hashing), SSIM (Structural Similarity).

## License

MIT
