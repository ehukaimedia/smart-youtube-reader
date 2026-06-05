# PR #13 Claude Opus Review

Date: 2026-06-05
Reviewer: Codex, with local headless Claude Code using `--model opus --effort max`
Reference: PR #13, `codex/fix-windows-start-npm`

## Scope

Claude reviewed the PR diff for Windows launcher correctness, process handling, Tailscale share-mode behavior, frontend/backend consistency, and test coverage.

## Initial Verdict

NO-GO.

Claude identified one blocking Windows launcher concern:

- `start.ps1`, frontend launch: the frontend process was started with `Start-Process -FilePath $NpmExe` where `$NpmExe` resolves to `npm.cmd`. With hidden launch and redirected output, routing `.cmd` shims directly through `Start-Process` can be fragile across Windows environments. Claude recommended starting the frontend through `$env:ComSpec /d /c` instead.

## Remediation

The frontend launch path was updated to route npm through `cmd.exe`:

- Build the frontend command as `"npm.cmd" run dev -- -H <host> --port 3001`.
- Start `$env:ComSpec` with `/d /c <command>`.
- Preserve hidden window behavior, working directory, log redirection, and process tracking.

## Validation

Local validation after remediation:

- PowerShell parser validation for `start.ps1`: passed.
- Launcher CI-equivalent scriptblock creation: passed.
- Backend targeted tests: `14 passed`.
- Backend ruff check: passed.
- Frontend lint: passed.
- Frontend production build: passed.

GitHub CI was green before the final launcher remediation. The branch should be pushed and the fresh CI run should be checked before merging.

## Residual Risk

The main remaining practical risk is environment-specific Windows browser or firewall behavior when using `start.bat -Share`. The PR now distinguishes local-only startup from share mode and only advertises the Tailscale URL when sharing is enabled.
