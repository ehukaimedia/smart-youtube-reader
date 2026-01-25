# Agent Integration Guide

**Smart YouTube Reader** is designed to be the "Eyes and Ears" for your AI Agents. By processing video content into structured data, it allows other agents (like Antigravity) to "watch" and "learn" from video tutorials.

## The Workflow

The integration follows a "Source -> Sinc" pattern:

1.  **Source (Smart YouTube Reader):**
    *   Downloads video.
    *   Generates `transcript.json` (Text).
    *   Extracts `frames/` (Visuals).
    *   Creates `archive.json` (Semantic Logic).

2.  **Sinc (Antigravity Agent):**
    *   Reads the `archive.json` to understand concepts.
    *   References `frames/` to "see" UI patterns.
    *   Generates code or `SKILL.md` files based on the video content.

## How to "Teach" Your Agent a Skill

If you have processed a tutorial video (e.g., "How to build X"), you can have your agent extract that knowledge into a reusable skill.

### 1. Identify the Data Path
Find the job ID for your processed video. The data will be located at:
`[Repo Root]/data/jobs/[slug]_[short_id]/`

*   **Archive:** `.../archive.json`
*   **Frames:** `.../frames/`

### 2. The Transfer Prompt
Copy and paste this prompt into your Agent's chat window:

> "I want you to learn a new capability from a video archive.
>
> **Source Path:** [Insert Absolute Path to Job Directory]
> **Task:** Analyze the `archive.json` in this directory.
>
> 1. **Extract Logic:** Read the `content` fields to understand the technical explanation.
> 2. **Extract Visuals:** Look at the referenced `images` in the `/frames` subdirectory to understand the UI/UX.
> 3. **Output:** Create a `SKILL.md` file that codifies this knowledge into a reusable agent skill."

## The "Learn from YouTube" Skill
If your agent is using the standard Antigravity Skills library, it likely already has the **Learn from YouTube Video** skill installed.

In that case, you only need to provide the Job ID:

> "Run the **Learn from YouTube Video** skill on Job ID: `antigravity-skills-are-a-cheat-code-new-system_05a53434`"

The agent will automatically locate the data in this repository and execute the learning process.
