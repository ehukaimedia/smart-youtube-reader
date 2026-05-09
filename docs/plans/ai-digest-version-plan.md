# AI Digest Version Plan

## Steps

1. Add backend schema support for digest creation requests and derived-project metadata.
2. Add a digest service that can call configured headless GPT 5.5 or Opus 4.7 agents and fall back to deterministic compaction.
3. Copy the source project into a new project directory, rewrite `archive.json` and `manifest.json`, and register the derived job as complete.
4. Add a reader UI model selector and `Create AI Digest Version` action.
5. Keep summary image metadata and dashboard thumbnail support for Codex-attached images without requiring app API credentials.
6. Require Codex-created summary images to be based on the current archive text and actual project frame images, not prompt-only generation.
7. Add a summary thumbnail CLI and make `Copy Codex Image Task` provide the exact command, avoiding long repeated prompts.
8. Mark AI digest projects on the dashboard while preserving existing share and download flows.
9. Update the architecture playground to document the new digest path.
10. Verify backend compilation, frontend typechecking, linting, and browser behavior.
