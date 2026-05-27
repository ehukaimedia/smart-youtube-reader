# Smart YouTube Reader - Frontend

This directory contains the Next.js frontend application for the Smart YouTube Reader. It provides a visual dashboard for managing jobs, reading structured transcripts and visual frames, and cutting/exporting video clips.

## Getting Started

For complete installation and setup instructions, please refer to the [Root README](../README.md).

### Quick commands

```bash
# Install dependencies
npm install

# Start development server
npm run dev -- --port 3001

# Run linting checks
npm run lint

# Build production bundle
npm run build
```

The frontend will run on `http://localhost:3001` and connects to the FastAPI backend running on `http://localhost:8001`.

## Tech Stack & Structure

* **Next.js & React**: App Router structure.
* **Styling**: Vanilla CSS.
* **Components**: Organized inside `src/app/` under specific route groups (`dashboard`, `reader/[jobId]`, `slicer/[jobId]`).
* **Icons**: Uses Lucide React.
