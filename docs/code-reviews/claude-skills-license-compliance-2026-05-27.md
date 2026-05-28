# Skills License Compliance Audit

**Date:** 2026-05-27
**Auditor:** Claude (`007cb622`)
**Scope:** Bundled skill content shipped on `origin/main` (commit `72b61ff`) — specifically the Impeccable-derived material and any Anthropic/Claude-derived skill content. Auxiliary check of the dirty working tree where it materially changes the redistribution surface.
**Repository LICENSE claim:** MIT (root `LICENSE` and `README.md` "This project is licensed under the MIT License").

---

## TL;DR

Two of the three bundled third-party trees on `origin/main` ship Apache 2.0-licensed derivative content **without** the LICENSE and NOTICE files Apache 2.0 §4 requires, and **without** the upstream attribution the source maintainer placed in `SKILL.md` frontmatter. The README's blanket "MIT" claim therefore misrepresents what the published repo actually distributes.

| Tree | Source | Upstream license | Published with required files? | Risk |
|---|---|---|---|---|
| `skills/impeccable/**` | `pbakaus/impeccable` (extends `anthropics/skills/skills/frontend-design`) | Apache 2.0 | **No** — missing LICENSE, missing NOTICE.md, missing `license:` line in SKILL.md frontmatter | **HIGH** |
| `skills/reference/**` | Modified copy of `skills/impeccable/reference/**` (19 of 35 files identical, 16 modified) | Apache 2.0 | **No** — no LICENSE or NOTICE; doesn't even self-identify as Impeccable-derived | **HIGH** |
| `skills/playground/**` | `anthropics/claude-plugins-official/plugins/playground` | Apache 2.0 | **Yes** — verbatim copy of upstream `LICENSE`, identical `plugin.json` (`author: Anthropic`) | **LOW** (note carried over from upstream) |
| `skills/smart-youtube-reader/SKILL.md` | Workspace original | Repo's MIT | n/a | **LOW** |
| `skills/youtube-archive-playground/SKILL.md` | Workspace original | Repo's MIT | n/a | **LOW** |

No legal conclusions are drawn beyond what the primary-source license texts plainly require. "Risk" below means *gap relative to what the upstream license text says about redistribution*.

---

## Primary Sources Used

| Upstream | Evidence path | Key text |
|---|---|---|
| `pbakaus/impeccable` | `LICENSE`, `NOTICE.md`, `skill/SKILL.md` (gh api `repos/pbakaus/impeccable`) | LICENSE = full Apache 2.0; NOTICE = "Impeccable / Copyright 2025-2026 Paul Bakaus", attributes Anthropic frontend-design (Apache 2.0, "Copyright 2025 Anthropic, PBC") and ehmo's typecraft-guide-skill; SKILL.md frontmatter: `license: Apache 2.0. Based on Anthropic's frontend-design skill. See NOTICE.md for attribution.` |
| `anthropics/skills/skills/frontend-design` | `LICENSE.txt`, `SKILL.md` (gh api `repos/anthropics/skills`) | LICENSE.txt = full Apache 2.0; SKILL.md frontmatter: `license: Complete terms in LICENSE.txt` |
| `anthropics/claude-plugins-official/plugins/playground` | `LICENSE`, `.claude-plugin/plugin.json` (gh api `repos/anthropics/claude-plugins-official`) | LICENSE = full Apache 2.0 (template, no copyright owner filled in); plugin.json `author: { name: "Anthropic", email: "support@anthropic.com" }` |
| `anthropics/claude-code` | `LICENSE.md` (gh api) | "© Anthropic PBC. All rights reserved. Use is subject to Anthropic's Commercial Terms of Service" — **proprietary, source-available**, not open source. Hosts a *different* `plugins/frontend-design/` snapshot under that proprietary license. Not the source for this repo's `skills/impeccable/**`. |

Apache 2.0 §4(a)-(d), summarized: any redistribution must (a) hand recipients a copy of the License, (b) carry prominent notice of modifications in modified files, (c) retain attribution notices from the original work, and (d) if a NOTICE file exists upstream, include a readable copy in the derivative.

---

## Findings

### F1 — HIGH — `skills/impeccable/**` redistributes Apache 2.0 code without LICENSE or NOTICE

**Evidence (origin/main `72b61ff`):**

- `git ls-tree origin/main skills/impeccable/` lists `SKILL.md`, `agents/openai.yaml`, the `reference/` and `scripts/` subtrees, and nothing else. No `LICENSE`, no `LICENSE.txt`, no `NOTICE`, no `NOTICE.md` exists anywhere under `skills/impeccable/`.
- `git show origin/main:skills/impeccable/SKILL.md | head -5` shows frontmatter with only `name` and `description`. The upstream `skill/SKILL.md` in `pbakaus/impeccable` carries:
  ```
  license: Apache 2.0. Based on Anthropic's frontend-design skill. See NOTICE.md for attribution.
  ```
  …which has been stripped from this copy.
- Upstream `NOTICE.md` contains required attribution to (1) Paul Bakaus (2025-2026), (2) Anthropic frontend-design (Apache 2.0, 2025 Anthropic, PBC), and (3) ehmo's typecraft-guide-skill. None of that text exists anywhere in the published repo.
- The file is **modified relative to upstream** without a §4(b) change notice: upstream template variables `{{command_prefix}}` and `{{scripts_path}}` have been pre-substituted (e.g. upstream `node {{scripts_path}}/load-context.mjs` is `node skills/impeccable/scripts/load-context.mjs` here; upstream `{{command_prefix}}impeccable teach` is `$impeccable teach` here). These are real, content-bearing edits, not just rendering.

**Why it matters:** Apache 2.0 §4(a) and §4(d) explicitly require that recipients of a derivative work receive a copy of the License and any upstream NOTICE. §4(b) additionally requires modified files to carry a prominent notice that they were changed. The repo's root `LICENSE` is MIT, which does not satisfy Apache 2.0's requirements. The README's flat "This project is licensed under the MIT License" further misrepresents what is being distributed. This is the part of the repo most exposed during a public-flip moment.

**Required actions (any of these closes the gap; the audit does not pick a path):**
1. Add `skills/impeccable/LICENSE` with the full Apache 2.0 text and `skills/impeccable/NOTICE.md` carrying the Impeccable + Anthropic + ehmo attributions verbatim from upstream `pbakaus/impeccable@main`. Restore the `license:` line in `SKILL.md` frontmatter. Confirm the README clarifies that `skills/impeccable/**` is Apache 2.0, distinct from the project's MIT code.
2. **Or** remove `skills/impeccable/**` from the repository entirely and tell users to install via the upstream `npx skills add pbakaus/impeccable` flow.

### F2 — HIGH — `skills/reference/**` is a partial, modified copy of the Impeccable reference tree

**Evidence:**

- Full-tree filename pair-up between `skills/reference/` and `skills/impeccable/reference/` on origin/main: 35 files pair by name; 19 are byte-identical (including `adapt.md` originally spot-checked); **16 differ**: `animate.md`, `audit.md`, `bolder.md`, `colorize.md`, `craft.md`, `critique.md`, `delight.md`, `distill.md`, `document.md`, `extract.md`, `live.md`, `overdrive.md`, `personas.md`, `quieter.md`, `shape.md`, `teach.md`. (Reproduce with the loop in §Verification.)
- A spot diff of one mismatch, `animate.md` line 32:
  ```
  upstream-like (impeccable/reference): If any of these are unclear from the codebase, {{ask_instruction}}
  modified  (reference):                  If any of these are unclear from the codebase, STOP and use Codex's
                                          structured user-input/question tool when available; if unavailable,
                                          ask directly in chat to clarify what you cannot infer.
  ```
  Template variables have been pre-substituted with Codex-specific text. This is a modification, not a rendering artifact.
- `skills/reference/` has no `SKILL.md`, no LICENSE, no NOTICE, and no top-level marker explaining what these files are. A fresh contributor reading the published repo cannot tell that this directory holds Apache-2.0-licensed third-party derivative content.

**Why it matters:** Same Apache 2.0 §4(a) and §4(d) obligations as F1 (LICENSE + NOTICE must travel with the redistribution), **plus** §4(b) because 16 files are modified — those modified files must carry a prominent notice of change. Two trees with the same lineage, two compliance surfaces, and an obvious failure mode (someone fixes F1 and forgets F2).

**Required actions (any of these closes the gap):**
1. Delete `skills/reference/**` entirely if it is redundant with `skills/impeccable/reference/**`. (Treat as user-owned: do not execute without operator approval; this audit is record-only per task scope.)
2. **Or** keep `skills/reference/**`, but add a top-level `skills/reference/README.md` and `skills/reference/LICENSE`/`NOTICE.md` mirroring the F1 fix, and add a §4(b) "Modified by Ehukai Media on YYYY-MM-DD: <one line summary>" notice at the top of each of the 16 modified files (or in the directory README if a per-file notice is impractical).

### F3 — LOW — `skills/playground/**` carries upstream LICENSE verbatim; one cosmetic carry-over

**Evidence:**

- `gh api repos/anthropics/claude-plugins-official/contents/plugins/playground/LICENSE` returns the same Apache 2.0 template (template-only, no `Copyright [yyyy] [name of copyright owner]` substitution) that ships at `skills/playground/LICENSE` in this repo.
- `gh api repos/anthropics/claude-plugins-official/contents/plugins/playground/.claude-plugin/plugin.json` matches `skills/playground/.claude-plugin/plugin.json` here, including `author: { name: "Anthropic", email: "support@anthropic.com" }`.
- The directory layout (`skills/playground/{LICENSE,README.md,.claude-plugin/plugin.json,skills/playground/SKILL.md,skills/playground/templates/*}`) is a faithful copy of `plugins/playground/` upstream.
- `anthropics/claude-plugins-official` itself has `license: null` in the repo metadata but ships per-plugin Apache 2.0 LICENSE files. This is the upstream's chosen pattern; it is not introduced by this repo.

**Why it matters:** Apache 2.0 §4 is satisfied here — the LICENSE file rides along with the redistributed code, the `plugin.json` author field credits Anthropic, and no upstream NOTICE file exists to mirror. The blank-template LICENSE is the upstream maintainer's posture, and a downstream redistributor should not edit it. The "low" risk note is the same blank-copyright template the upstream chose; if it ever needs to be filled in, that is an upstream conversation, not a Ehukai Media one.

**Required actions:** None for Apache 2.0 compliance. **Optional**: add a one-line note to `skills/playground/README.md` (or the project's root README "Sharing" / "Bundled skills" section) saying "vendored from `anthropics/claude-plugins-official/plugins/playground`, licensed Apache 2.0" so a fresh contributor doesn't conflate this tree with the repo's MIT-licensed code.

### F4 — MEDIUM — Root `LICENSE` and `README.md` claim MIT for the whole repo while shipping Apache 2.0 third-party content

**Evidence:**

- Root `LICENSE`: "MIT License / Copyright (c) 2026 Ehukai Media …".
- `README.md:236-238`: "## License / This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details."
- `skills/impeccable/**`, `skills/reference/**`, and `skills/playground/**` are not Ehukai-Media-authored MIT content; they are Apache 2.0 derivatives bundled in the same repo.

**Why it matters:** MIT and Apache 2.0 can co-exist in one distribution (Apache 2.0 is one-way compatible with most permissive licenses), but the README's unqualified MIT claim is misleading once Apache 2.0 third-party code is bundled. A downstream user can reasonably assume everything in the repo is MIT and reuse Impeccable text under MIT terms — which is not what the upstream license grants. This is also the easiest finding to fix without touching the third-party trees.

**Required actions:**
- In `README.md` §License (and ideally a new "Bundled third-party skills" sub-section), call out that `skills/impeccable/**`, `skills/reference/**`, and `skills/playground/**` are Apache 2.0 with their own LICENSE / NOTICE per-tree. Once F1 and F2 are resolved, that subsection can link to those per-tree LICENSE/NOTICE files.

### F5 — LOW — Working-tree-only: `skills/playground/impeccable/SKILL.md` references a missing `NOTICE.md`

**Evidence:**

- The working tree (not published) contains an untracked `skills/playground/impeccable/SKILL.md` whose frontmatter declares:
  ```
  license: Apache 2.0. Based on Anthropic's frontend-design skill. See NOTICE.md for attribution.
  ```
- No `NOTICE.md` exists alongside this file or anywhere under `skills/playground/impeccable/`.
- This is a *local move* of the Impeccable skill into the playground plugin tree. It is **not** present on `origin/main` and is explicitly classified as user-owned (see `docs/code-reviews/sonnet-regression-context-audit-2026-05-27.md`).

**Why it matters:** This file is not currently part of the published artifact, so it does not change the public compliance surface today. But if the operator later promotes this move into a tracked commit, the dangling `See NOTICE.md` reference will produce the same F1-class violation in a new path. Surfacing it here so the move-to-track decision happens with eyes open. Per task scope, this audit makes no edits to this user-owned file.

**Required actions:** Informational only. If the operator decides to track this move, ensure the same fix described in F1 is applied to the new path (LICENSE + NOTICE.md + restored frontmatter `license:` line) before commit.

### F6 — LOW — Anthropic/Claude-derived material: only `skills/impeccable/**` and `skills/playground/**` qualify

**Evidence:**

- `skills/smart-youtube-reader/SKILL.md` and `skills/youtube-archive-playground/SKILL.md` are workspace-original content. No upstream Anthropic provenance is claimed in their frontmatter or body text. The grep for Anthropic-derivative markers (`frontend-design`, `Apache`, `Anthropic`, copyright headers) on these two files turned up nothing material.
- The only Anthropic/Claude-derived material on `origin/main` is therefore (a) the Impeccable-via-frontend-design lineage covered by F1/F2, and (b) the playground plugin covered by F3.
- Local `.ehukaiconnect/skills/**` and `.claude/**` are gitignored and not part of the published repo (`.gitignore:9 .claude/` and the entire `.ehukaiconnect` tree is untracked).

**Why it matters:** Confirms the audit's surface is bounded. No additional Anthropic-licensed content is being silently distributed elsewhere.

**Required actions:** None.

---

## Verification Commands (reproducible)

```bash
# Published surface
git fetch origin main
git ls-tree -r origin/main --name-only | grep -E '^(skills/|LICENSE|NOTICE)'

# Show the Impeccable frontmatter actually shipped on main
git show origin/main:skills/impeccable/SKILL.md | sed -n '1,5p'

# Full-tree pairing: how many files in skills/reference/ differ from
# the matching file in skills/impeccable/reference/ on origin/main?
total=0; mismatches=0
while IFS= read -r f; do
  total=$((total+1))
  base=$(basename "$f")
  diff -q <(git show "origin/main:$f") \
          <(git show "origin/main:skills/impeccable/reference/$base") \
          >/dev/null 2>&1 || mismatches=$((mismatches+1))
done < <(git ls-tree -r origin/main --name-only skills/reference/)
echo "$mismatches / $total files modified"   # observed: 16 / 35

# Upstream Impeccable LICENSE + NOTICE + frontmatter
gh api -H "Accept: application/vnd.github.raw" \
  repos/pbakaus/impeccable/contents/NOTICE.md
gh api -H "Accept: application/vnd.github.raw" \
  repos/pbakaus/impeccable/contents/skill/SKILL.md | head -12

# Upstream frontend-design LICENSE.txt and frontmatter
gh api -H "Accept: application/vnd.github.raw" \
  repos/anthropics/skills/contents/skills/frontend-design/LICENSE.txt | head -5
gh api -H "Accept: application/vnd.github.raw" \
  repos/anthropics/skills/contents/skills/frontend-design/SKILL.md | head -5

# Upstream playground plugin (Apache 2.0; verbatim copy here)
gh api repos/anthropics/claude-plugins-official/git/trees/main?recursive=1 \
  --jq '.tree[] | select(.path | test("^plugins/playground")) | .path'
```

---

## Scope Limits

- This audit reads the published artifact and authoritative upstream source files. It does **not** offer legal advice; "Apache 2.0 §4 requires X" statements quote the license text directly.
- Per task instruction, no skill files were edited or removed. The audit is the only file added.
- Local untracked state is referenced (F5) only where it materially affects future redistribution decisions.
