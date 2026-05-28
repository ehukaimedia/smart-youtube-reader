# Repo Compliance Scan - 2026-05-27

**Reviewer:** Codex
**Scope:** Public release surface at `origin/main` (`72b61ff`, PR #9 merge), plus a separate check of the operator-owned local skill relocation in the primary worktree.
**Decision before remediation:** **NO-GO until bundled skill attribution is fixed.**

**Remediation note:** The same branch that carries this audit also adds third-party notices, per-tree Apache license/NOTICE files for Impeccable-derived material, README license clarification, and modification notices for the adapted `skills/reference/**` files.

This is an engineering compliance audit, not legal advice. I checked the repository for open-source license attribution gaps, obvious secrets, generated artifacts, stale regression context, binary bloat, and dependency-license signals.

## Required Actions

### 1. Critical - Bundled Impeccable skill material is redistributed without its Apache license and NOTICE

**Files:** `skills/impeccable/**`, `skills/reference/**`, `README.md:238`
**Confidence:** High

The published repo contains 52 tracked files under `skills/impeccable/` and 35 tracked files under `skills/reference/`. The content is Impeccable skill material or duplicated Impeccable reference material. Upstream Impeccable is Apache-2.0 and explicitly points to a NOTICE attribution chain for Anthropic's `frontend-design` skill and Typecraft additions.

Local evidence:

- `find . -name LICENSE -o -name NOTICE -o -name 'NOTICE*' -o -name 'COPYING*'` finds only `LICENSE` and `skills/playground/LICENSE`.
- `find skills/impeccable -maxdepth 3 -type f \( -iname '*license*' -o -iname '*notice*' -o -iname '*copying*' \)` returns no files.
- `cmp -s skills/impeccable/reference/typography.md skills/reference/typography.md` returns identical content, confirming the top-level `skills/reference/` tree is also in the Impeccable-derived release surface.
- `README.md:238` currently says the project is MIT only, which is incomplete while Apache-2.0-derived skill content is bundled.

Primary-source evidence:

- Impeccable's GitHub page labels the repository Apache-2.0 and its README says to see `NOTICE.md` for attribution.
- Impeccable's `NOTICE.md` attributes the skill to Paul Bakaus, states it builds on Anthropic's original `frontend-design` skill, cites Apache-2.0 for that original work, and notes Typecraft Guide additions.
- Impeccable's `LICENSE` is Apache-2.0 with `Copyright 2025 Paul Bakaus`.
- Anthropic's `skills/frontend-design/LICENSE.txt` is Apache-2.0.

**Required fix:** Add third-party license and notice coverage before publishing further. The cleanest path is:

1. Add a root `NOTICE.md` or `THIRD_PARTY_NOTICES.md`.
2. Include Impeccable attribution covering both `skills/impeccable/**` and `skills/reference/**`.
3. Preserve Impeccable's NOTICE attribution chain, including Anthropic `frontend-design` and Typecraft Guide notes.
4. Add an explicit README license note: project code is MIT except bundled third-party skill/vendor material covered by the notices.

Alternative: remove `skills/impeccable/**` and `skills/reference/**` from the public repo until the provenance and notices are intentionally added.

### 2. High - Vendored `modern-screenshot` is MIT-licensed but its license text is not carried

**Files:** `skills/impeccable/scripts/modern-screenshot.umd.js`, `skills/impeccable/scripts/live-server.mjs:230`
**Confidence:** High

The repository redistributes a vendored `modern-screenshot` browser build. The vendored file is byte-identical to `modern-screenshot@4.7.0` `package/dist/index.js`.

Local evidence:

- `shasum -a 256 skills/impeccable/scripts/modern-screenshot.umd.js` equals `bb36665889124a0b6e15f16045265737449c3bdcf2712cdb08af3cfa01563e2b`.
- `tar -xOf /tmp/modern-screenshot-4.7.0.tgz package/dist/index.js | shasum -a 256` returns the same hash.
- `skills/impeccable/scripts/live-server.mjs:230` documents it as a vendored UMD build.
- No vendored MIT license text is present in `skills/impeccable/` or root notices.

Primary-source evidence:

- `modern-screenshot` `package.json` declares `license: "MIT"`.
- Its upstream license includes `Copyright (c) 2021-present wxm`.

**Required fix:** Add `modern-screenshot` to root `NOTICE.md` or `THIRD_PARTY_NOTICES.md`, including the MIT license text/copyright, or replace the vendored file with an npm dependency where the package license is installed and distributed appropriately.

### 3. Medium - `skills/playground` has Apache text but weak provenance

**Files:** `skills/playground/**`, `skills/playground/.claude-plugin/plugin.json:5`, `skills/playground/LICENSE`
**Confidence:** Medium

The `skills/playground` plugin contains an Apache-2.0 license file and the plugin manifest lists Anthropic as author. I did not find `skills/playground` in the current public `anthropics/skills` tree during the scan, so the source and exact copyright provenance are not fully documented in this repo.

**Recommended fix:** Add this skill to the same third-party notices file with source/provenance if known. If it came from a specific Anthropic release, record that upstream URL/commit and license. If it is Ehukai-authored from an Apache template, say that explicitly.

### 4. Medium - Local untracked skill relocation is unsafe to publish as-is

**Files:** primary worktree only, `skills/playground/impeccable/**`
**Confidence:** High

This is not in public `origin/main`, but it matters if the operator later commits the local skill move.

Local evidence:

- Primary worktree has 52 tracked deletions under `skills/impeccable/`.
- Primary worktree has 51 untracked files under `skills/playground/impeccable/`.
- `skills/playground/impeccable/SKILL.md` says `license: Apache 2.0. Based on Anthropic's frontend-design skill. See NOTICE.md for attribution.`
- `find skills/playground/impeccable -maxdepth 3 -type f \( -iname '*license*' -o -iname '*notice*' -o -iname '*copying*' \)` returns zero files.

**Required before committing that move:** add/preserve the Impeccable license and NOTICE files, plus the `modern-screenshot` MIT notice if that vendored file remains in the moved tree.

## Clean Findings

- No obvious high-signal secrets in tracked public files. Targeted scan for AWS, Google API, OpenAI-style, GitHub PAT, Slack token, and private-key patterns returned no hits.
- No tracked `.pyc`, `__pycache__`, `.pytest_cache`, `.next`, `node_modules`, `.DS_Store`, or `data/jobs` artifacts.
- No tracked media/binary bloat matched `png`, `jpg`, `webp`, `mp4`, `pdf`, archive, or similar generated-file patterns.
- Repo size is small: clean worktree is about 2.2 MB, with `skills/` about 1.2 MB.
- Existing regression-context audit remains valid: active code is clean of old Ollama implementation references; remaining Ollama mentions are migration docs, specs prohibiting old behavior, or superseded reviews.
- Frontend npm lockfile includes LGPL/MPL/CC-BY transitive packages from normal npm dependencies, especially `@img/sharp-libvips-*`, `axe-core`, and `caniuse-lite`. These are not vendored source in this repo, but binary/container distribution should include dependency notices.

## Commands Run

```bash
git fetch origin main
git status --short --branch
git rev-parse --short origin/main
find . -name LICENSE -o -name NOTICE -o -name 'NOTICE*' -o -name 'COPYING*' | sort
find skills -maxdepth 4 -type f | sort
rg -n --hidden --glob '!.git' --glob '!frontend/package-lock.json' '(Copyright|License|Apache|MIT|GPL|AGPL|LGPL|BSD|MPL|NOTICE|Anthropic|Claude|impeccable|source-available|All rights reserved|proprietary)'
rg -n --hidden --glob '!.git' --glob '!frontend/package-lock.json' '(AKIA[0-9A-Z]{16}|AIza[0-9A-Za-z_-]{35}|sk-[A-Za-z0-9]{20,}|ghp_[A-Za-z0-9]{36,}|github_pat_[A-Za-z0-9_]{20,}|-----BEGIN (RSA|DSA|EC|OPENSSH|PRIVATE) KEY-----|xox[baprs]-[A-Za-z0-9-]{10,})' .
git ls-files | rg '(^|/)(__pycache__|\.pytest_cache|\.next|node_modules|data/jobs|\.DS_Store)|\.(pyc|pyo)$'
git ls-files | rg '\.(pyc|pyo|DS_Store|zip|tar|gz|mp4|mov|mkv|webm|png|jpg|jpeg|gif|webp|pdf)$'
find skills/impeccable -maxdepth 3 -type f \( -iname '*license*' -o -iname '*notice*' -o -iname '*copying*' \) -print
cmp -s skills/impeccable/reference/typography.md skills/reference/typography.md
diff -qr skills/impeccable/reference skills/reference | head -100
gh api repos/pbakaus/impeccable --jq '{full_name,html_url,license:.license.spdx_id,default_branch}'
gh api repos/pbakaus/impeccable/contents/NOTICE.md --jq '.content' | base64 --decode
gh api repos/anthropics/skills/contents/skills/frontend-design/LICENSE.txt --jq '.content' | base64 --decode
npm view modern-screenshot name version license homepage repository.url --json
npm pack modern-screenshot@4.7.0 --json --pack-destination /tmp
tar -xOf /tmp/modern-screenshot-4.7.0.tgz package/dist/index.js | shasum -a 256
node - <<'NODE'
const lock=require('./frontend/package-lock.json');
const counts={};
for (const [name,pkg] of Object.entries(lock.packages||{})) {
  if (!name || !name.startsWith('node_modules/')) continue;
  const lic=pkg.license || 'NOASSERTION';
  counts[lic]=(counts[lic]||0)+1;
}
console.log(JSON.stringify(counts,null,2));
NODE
```

## Sources

- Impeccable repository: https://github.com/pbakaus/impeccable
- Impeccable license: https://github.com/pbakaus/impeccable/blob/main/LICENSE
- Impeccable notice: https://github.com/pbakaus/impeccable/blob/main/NOTICE.md
- Anthropic `frontend-design` license: https://github.com/anthropics/skills/blob/main/skills/frontend-design/LICENSE.txt
- `modern-screenshot` package: https://github.com/qq15725/modern-screenshot
- `modern-screenshot` license: https://github.com/qq15725/modern-screenshot/blob/main/LICENSE
