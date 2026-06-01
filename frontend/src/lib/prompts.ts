// Single source of truth for the agent-facing prompt/task text copied from the
// dashboard and reader. The AI-digest-with-images task in particular was
// duplicated byte-for-byte across both pages; centralizing it here prevents drift.

// dataFolderName is intentionally loose: the reader calls these without guarding
// (matching the original inline template literals, which coerced undefined/null).
export function aiDigestPaths(dataFolderName: string | null | undefined): { projectFolder: string; draftPath: string } {
  const projectFolder = `data/jobs/${dataFolderName}`;
  const draftPath = `${projectFolder}/generated/ai-digest-draft.json`;
  return { projectFolder, draftPath };
}

export function buildAiDigestWithImagesTask(dataFolderName: string | null | undefined): string {
  const { projectFolder, draftPath } = aiDigestPaths(dataFolderName);
  return `Create the default Smart YouTube Reader AI digest version with generated WebP teaching images for this project using the local CLI.

Do not use an in-app model option. You are the digest-and-image agent. Codex GPT 5.5 image generation is the recommended setup.
Run commands from the smart-youtube-reader repo root.

Important:
- Infographic style is a human choice. Before generating images, set one style for the whole digest:
  - simple: use .codex/skills/simple-infographic for quiet text-led card-strip teaching images.
  - premium: use .codex/skills/premium-infographic and GPT 5.5 image generation for full-color, concept-adaptive visual-learning images that teach the chapter idea.
  If the human has not chosen, pick the style that best fits the material and record the choice in operator_image_note.
- Read archive.json and inspect the attached frame images before deciding what to keep.
- Create a new digestible chapter structure, not a light paraphrase.
- Create one novel generated WebP teaching image per digest chapter.
- Keep the digest to at most 6 chapters/images. If the material truly needs more than 6 images, explain the needed count in operator_image_note and still produce the best 6-image digest.
- Do not copy, crop, trace, or reuse source frames, screenshots, or YouTube thumbnails.
- Do not include fake plus buttons, carousel arrows, pagination dots, or navigation controls inside static infographic images.
- Save and reference only generated/*.webp output images in the draft.

Workflow:
1. Run this command to print the default image-rich digest task:
   python3 tools/create_ai_digest_version.py "${projectFolder}"
2. Read archive.json and inspect the attached frame images as evidence.
3. Cut fluff, repetition, sponsor chatter, intros/outros, and low-value transitions.
4. Preserve durable facts, theory, procedures, examples, caveats, failure modes, and useful visual explanations.
5. Save the generated WebP images under:
   ${projectFolder}/generated/
6. Write the required JSON draft to:
   ${draftPath}
7. Materialize the new AI digest project:
   python3 tools/create_ai_digest_version.py "${projectFolder}" --draft "${draftPath}"
8. Verify the dashboard shows the new project with an AI Digest badge and the reader opens it with one generated image per chapter.

Source project:
${projectFolder}`;
}

export function buildAiDigestTextOnlyTask(dataFolderName: string | null | undefined): string {
  const { projectFolder, draftPath } = aiDigestPaths(dataFolderName);
  return `Create a text-only Smart YouTube Reader AI digest version for this project using the local CLI.

Do not use an in-app model option. You are the digest agent.
Run commands from the smart-youtube-reader repo root.

Workflow:
1. Run this command to print the text-only digest task:
   python3 tools/create_ai_digest_version.py "${projectFolder}" --text-only
2. Read archive.json and inspect the attached frame images before deciding what to keep.
3. Cut fluff, repetition, sponsor chatter, intros/outros, and low-value transitions.
4. Preserve durable concepts, procedures, definitions, examples, caveats, and useful visual explanations.
5. Write the required JSON draft to:
   ${draftPath}
6. Materialize the new AI digest project:
   python3 tools/create_ai_digest_version.py "${projectFolder}" --draft "${draftPath}"
7. Verify the dashboard shows the new project with an AI Digest badge and the reader opens it.

Source project:
${projectFolder}`;
}

export function buildGroupAiDigestTask(projectFolders: string[], groupTitle: string): string {
  const quotedProjects = projectFolders.map(path => `"${path}"`).join(' ');
  return `Create a Smart YouTube Reader GROUP AI digest using the local CLI.

Do not use an in-app model option. You are the group digest agent.
Run commands from the smart-youtube-reader repo root.

Important: this is not a source-frame merge. Read all source archives and inspect the attached frame images as evidence, then create one novel, intuitive combined transcript and exactly 3 novel WebP AI teaching images from that new transcript.

Infographic style is a human choice. Before generating images, set one style for the whole group digest:
- simple: use .codex/skills/simple-infographic for quiet text-led card-strip teaching images.
- premium: use .codex/skills/premium-infographic and GPT 5.5 image generation for full-color, concept-adaptive visual-learning images that teach the combined lesson.
If the human has not chosen, pick the style that best fits the material and record the choice in the image prompts.

Teaching goal:
- Teach digestible facts, theory, and testable hypotheses.
- Do not concatenate or lightly paraphrase the source transcripts.
- Build a new mental model that explains what is true, why it works, when it fails, and what evidence confirms it.

Workflow:
1. Run this command to print the exact group digest task:
   python3 tools/create_group_ai_digest_version.py ${quotedProjects} --title "${groupTitle || 'Combined Learning Digest'}"
2. Read every archive.json and inspect the attached frame images before deciding what to keep.
3. Merge repeated lessons across videos into a new transcript with chapter-level facts, theory, and hypotheses. Cut fluff, repetition, intros/outros, and low-value transitions.
4. Create exactly 3 new WebP AI teaching images from the new combined transcript. Do not copy original frames, screenshots, or YouTube thumbnails into the output. Do not include fake plus buttons, carousel arrows, pagination dots, or navigation controls inside static infographic images.
5. Write the required JSON draft and the 3 generated WebP images to the staging paths printed by the CLI.
6. Materialize the group AI digest with the command printed by the CLI.
7. Verify the dashboard shows the new project with a Group AI Digest badge and the reader opens it.

Source projects:
${projectFolders.join('\n')}`;
}

export function buildLearningPrompt(params: {
  title?: string | null;
  id: string;
  videoUrl?: string | null;
  archiveUrl: string;
  baseUrl: string;
}): string {
  const { title, id, videoUrl, archiveUrl, baseUrl } = params;
  return `You have access to a structured archive of a YouTube video.

Video: "${title || id}"
YouTube: ${videoUrl || '(not available)'}
Archive JSON: ${archiveUrl}

Each chapter in the archive has:
- concept: topic title
- summary: one-sentence overview
- content: compact transcript-grounded teaching evidence for the section
- timestamp_start / timestamp_end: seconds into the video
- images: array of frame filenames — fetch and read these, they often contain slides, diagrams, and visual explanations that are NOT in the transcript text

To read a frame image: ${baseUrl}/<filename>  (e.g. ${baseUrl}/frames/0007.png)
To jump to a section on YouTube: append &t=<timestamp_start> to the YouTube URL

Start by fetching the archive JSON, then for each chapter read both the content text AND the frame images — this video likely uses visual slides to explain its concepts.

What would you like to know about this video?`;
}
