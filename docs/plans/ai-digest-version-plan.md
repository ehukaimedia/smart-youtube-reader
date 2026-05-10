# AI Digest Version Plan

## Steps

1. Remove backend-hosted local Gemma and deterministic digest generation.
2. Add a digest CLI that prints an external-agent task and materializes a digest from an agent-authored JSON draft.
3. Copy the source project into a new project directory, rewrite `archive.json` and `manifest.json`, and let the job store discover the derived job from disk.
4. Replace the reader UI model selector with `Copy AI Digest CLI Task`.
5. Keep summary image metadata and dashboard thumbnail support for Codex-attached images without requiring app API credentials.
6. Require Codex-created summary images to be based on the current archive text and actual project frame images, not prompt-only generation.
7. Add a summary thumbnail CLI and make `Copy Codex Image Task` provide the exact command, avoiding long repeated prompts.
8. Mark AI digest projects on the dashboard while preserving existing share and download flows.
9. Update the architecture playground to document the new digest path.
10. Verify backend compilation, frontend typechecking, linting, and browser behavior.
11. Verify the digest CLI against a synthetic draft and ensure invalid drafts fail without modifying the source project.
