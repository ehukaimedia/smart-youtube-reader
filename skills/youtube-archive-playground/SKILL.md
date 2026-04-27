---
name: youtube-archive-playground
description: Creates an interactive single-file HTML playground from a smart-youtube-reader job archive. Use this whenever an agent or user wants to visually explore a completed YouTube reader job — browsing chapters, viewing operator-curated frames, and generating focused prompts for downstream agents. Trigger when the user says "make a playground", "explore the job", "browse the archive", "create an explorer", or "visualize the video" for a smart-youtube-reader job, or when an agent needs to turn a job's archive.json into a shareable interactive artifact.
---

# YouTube Archive Playground

A playground is a self-contained HTML file that reads a job's `archive.json` and lets you browse chapters, view frames, filter by concept, and copy a focused agent prompt about the selected content. No server required after generation — open the file in any browser.

## What it produces

A single `.html` file that:
- Lists all archive chapters in a scrollable panel with their concept titles and timestamps
- Displays the selected chapter's summary, full content, and operator-curated frames (images served via the local API)
- Filters chapters by keyword search in real time
- Outputs a ready-to-copy agent prompt scoped to the selected chapter(s)
- Works offline once the HTML is open (images load from `http://localhost:8001` if the server is running)

## How to build it

### Step 1: Get the archive data

Read the job's archive and manifest:

```
GET http://localhost:8001/jobs/<job_id>
```
→ get `data_folder_name` from the response

```
GET http://localhost:8001/data/jobs/<data_folder_name>/archive.json
```
→ full chapter list

```
GET http://localhost:8001/data/jobs/<data_folder_name>/manifest.json
```
→ video title, URL, chapter count

### Step 2: Embed and write the HTML

Inline the archive data directly as a JS variable — the playground is self-contained, no fetch needed after generation.

```javascript
const ARCHIVE = { /* paste full archive.json contents here */ };
const JOB_META = { title: "...", url: "...", folder: "..." };
const API_BASE = "http://localhost:8001";
```

**Security — always escape the JSON before inlining.** The string `</script>` anywhere in the archive content (e.g., a code snippet in a chapter's `content` field) will close the `<script>` block mid-parse, corrupting the file or enabling script injection. Escape it when serialising in Python:

```python
import json
archive_json = json.dumps(archive_data, ensure_ascii=False).replace('</', '<\\/')
```

Or if writing the HTML in JavaScript/Node:

```javascript
const archiveJson = JSON.stringify(archiveData).replace(/<\//g, '<\\/');
```

This single substitution makes the embedding safe regardless of what text the archive contains.

### Step 3: Build the layout

Use a three-panel layout:

```
┌─────────────────┬──────────────────────────┬──────────────────┐
│  Chapter List   │   Chapter Detail         │  Agent Prompt    │
│  (scrollable)   │   concept + content      │  (copy button)   │
│                 │   + frames               │                  │
│  [ search box ] │                          │                  │
└─────────────────┴──────────────────────────┴──────────────────┘
```

Or on narrow screens: stacked vertically (list → detail → prompt).

### Step 4: Chapter list panel

Each chapter item shows:
- Concept title (bold)
- Timestamp range formatted as `MM:SS – MM:SS`
- Frame count badge if images exist
- Highlight selected chapter

Clicking selects it. The search box filters by concept title or content text.

### Step 5: Chapter detail panel

When a chapter is selected, display:
- Concept title + timestamp link (YouTube deep-link using `video_url + &t=<timestamp_start>`)
- Summary (italic, muted color)
- Full content paragraph
- Image grid: load each image path from `ARCHIVE.archive[n].images` using `${API_BASE}/data/jobs/${JOB_META.folder}/${imagePath}`

If the server isn't running, images show a broken-image placeholder — that's fine.

### Step 6: Agent prompt panel

The prompt panel has two modes: a **global learning prompt** (always visible) and a **chapter prompt** (selected chapter).

**Global learning prompt** — shown at the top of the panel, always available:

```javascript
function buildGlobalPrompt() {
  return `You have access to a structured archive of a YouTube video.

Video: "${JOB_META.title}"
YouTube: ${JOB_META.url}
Archive JSON: ${API_BASE}/data/jobs/${JOB_META.folder}/archive.json

The archive contains ${ARCHIVE.archive.length} semantic chapters. Each chapter has:
- concept: topic title
- summary: one-sentence overview
- content: full transcript text for the section
- timestamp_start / timestamp_end: seconds into the video
- images: video frame filenames (served at ${API_BASE}/data/jobs/${JOB_META.folder}/<filename>)

To learn from this video: fetch the archive JSON, read through the chapters by concept, and append &t=<timestamp_start> to the YouTube URL to jump to any section.

What would you like to know about this video?`;
}
```

Include a **Copy Learning Prompt** button at the top of the panel that copies this global prompt. This is the primary sharing mechanism — paste into any LLM chat and it immediately knows how to learn from the video.

**Chapter-focused prompt** — shown when a chapter is selected, for drilling into a specific section. Generate a focused prompt for the selected chapter. Use natural language, not a data dump:

```javascript
function buildPrompt(chapter) {
  const ts = formatTime(chapter.timestamp_start);
  const imgNote = chapter.images?.length
    ? ` Visual evidence includes ${chapter.images.length} frame(s) at this timestamp.`
    : '';
  return `From the video "${JOB_META.title}" (${ts}):

Topic: ${chapter.concept}
Summary: ${chapter.summary}

${chapter.content}${imgNote}

Based on this section, `;
}
```

The trailing "Based on this section, " primes the agent to continue with a specific question. The user edits the ending before copying.

Include a **Copy** button (clipboard API, brief "Copied!" flash) and an **editable textarea** so the user can append their question before copying.

When multiple chapters are selected (hold Shift or Ctrl to multi-select), concatenate them with section headers and summarize the span: `"Covers timestamps X:XX – Y:YY"`.

### Step 7: Controls

Minimal controls in a top bar:
- **Search** — real-time filter on the chapter list
- **Include images note** toggle — adds/removes the frame reference from the prompt
- **Select All / Clear** — for multi-chapter prompt building

No unnecessary controls. Keep it fast to use.

## Visual style

Follow the playground skill's dark theme conventions:
- Background: `#0f0f0f`, card: `#1a1a1a`, border: `#2a2a2a`
- Accent: `#7c6af7` (purple, matching the app's `--secondary`)
- System font for UI, monospace for code snippets in the prompt output
- Selected chapter: left border accent, slightly lighter background
- Responsive: min-width 320px, comfortable at 1200px+

## State management

```javascript
const state = {
  chapters: [],        // from ARCHIVE.archive
  selected: new Set(), // selected chapter indices
  search: '',
  includeImageNote: true,
};

function updateAll() {
  renderChapterList();
  renderDetail();
  renderPrompt();
}
```

## Opening the file

After writing the HTML file, save it inside the job's data directory and open it:

```
data/jobs/<folder>/playground.html
```

```bash
open data/jobs/<folder>/playground.html
```

The job folder already namespaces it — no need to repeat the slug in the filename.

## Common mistakes

- Hardcoded image URLs that break if the folder name changes — always use `JOB_META.folder` dynamically
- No YouTube deep-link on chapter titles — always add `&t=<timestamp>` (not `?t=`) since YouTube watch URLs already have `?v=...` as their query param
- Prompt is just a JSON dump of the chapter — write it as natural language a human or agent can read and act on
- No fallback when images 404 — add `onerror="this.style.opacity=0.2"` on `<img>` tags
- Forgetting to embed the archive inline — the file must work offline after generation
- Forgetting to escape `</` in the inlined JSON — causes silent breakage if any chapter content contains a closing script tag
- Empty archive — if `archive.json` has no chapters, render a message (`"This archive has no chapters yet"`) instead of an empty panel
- Not auto-selecting the first chapter on load — the playground should show useful content immediately, not an empty detail panel
