# ART First-Push Readiness — `art-0-integrated`, 2026-07-21

Prepared per explicit instruction to verify ART's integration branch for its first remote push.
**No push, no tag, no merge to main performed while preparing this packet.** This document is a
decision input for Omer, not an executed action. This file lives in the ART repo deliberately —
the HarnessKit repo/evidence packet (`evidence/PUSH_READINESS_2026-07-20.md`) was not touched by
this batch, per explicit instruction.

## 1. Local state, verified live

- Worktree: `C:/Dev/art-worktrees/art-integration`
- Branch: `art-0-integrated`
- HEAD: `9f10a9daa43b107543e948a7fe0c573074d02e07` (short `9f10a9d`) — **matches the expected HEAD
  exactly.**
- `git status --short`: clean, before and after every check in this packet.
- No stash in this worktree (the disclosed HarnessKit stash, `stash@{0}` on
  `hk/phase-a-v1-integration`, lives in a different repo entirely and was never referenced).
- Other ART worktrees, confirmed unchanged: `art-0-vertical-slice` at `6919e5a` (clean),
  `ts-js-agent-lint-slice` at `c9a56bf` (clean) — both fully-merged ancestors, nothing to push
  independently.
- Main checkout (`C:/Dev/agent-reliability-toolkit`, branch `claude/read-and-plan-2an34e` @
  `731ac89`) confirmed to carry only its pre-existing, previously-disclosed, unrelated dirt —
  `M .harnesskit/workflow-dag.json`, `?? .harnesskit/workflow-final-report.json` — untouched by
  this batch, not part of this push in any form.

## 2. Full tests, real re-run at `9f10a9d`

All run from `packages/agent-lint`, `.venv` active (`python.exe` at
`packages/agent-lint/.venv/Scripts/python.exe`):

- `python tools/art_rule_test.py` → **`OK: 54 fixture case(s) across 3 rule(s)`**.
- `python -m pytest -q` → **228 passed, 1 skipped, 1 failed.** The failure is the same
  pre-existing, disclosed gap as the prior evidence cycle:
  `TestHostileFilenames::test_all_hostile_filenames_are_handled` — only 2 of 4 expected fixture
  files are committed under `fixtures/malicious/hostile_filenames/` (a fixture-data gap, not a
  code defect; unrelated to this branch's diff). The previously-flaky
  `TestPerFileTimeBudget::test_zero_budget_aborts_before_lowering` passed clean this run — the
  flakiness itself was already disclosed and is not new.
- `ruff check .` → all checks passed. `ruff format --check .` → 68 files already formatted.
  `mypy src` → no issues found in 35 source files.
- TS/JS worker-reuse tests (`tests/lint/frontend/test_ts_js_frontend.py`) re-run **5x in
  isolation**: 15 passed every time, 0 flakes.
- Real scan of HarnessKit's full tree (`agent-lint scan C:/Dev/hk-worktrees/phase-a-v1-integration`,
  no `--json` flag exists on this CLI — corrected from the prior evidence packet's implied usage):
  **14 findings**, all `[HIGH] AR001` (unbounded-recursion pattern), ~2.0s runtime, zero
  scan-limit diagnostics. Consistent with the prior cycle's "14 findings" count.

## 3. Security / privacy checks, re-run against the same diff range (`cdecce0..9f10a9d`)

- `git diff cdecce0..9f10a9d | grep -inE` for API-key-shaped strings (`sk-`, `AKIA`, `ghp_`,
  `xox[baprs]-`, `key=`/`secret=`/`password=`/`token=` assignment patterns): **0 matches.**
- PEM/PGP key headers (`BEGIN ... PRIVATE KEY`, `BEGIN PGP`): **0 matches.**
- Local filesystem paths containing the real machine's username, including the Hebrew-alphabet
  segment (`עומר`), checked explicitly: **0 matches.**
- `git ls-files | grep -c node_modules`: **0** — confirmed untracked.

## 4. Rollback verification, real (not asserted)

An out-of-order revert test surfaced a nuance the prior evidence cycle's phrasing glossed over,
worth stating precisely rather than repeating as-is:

- `git revert --no-commit f5b3be9` **against the current tip** (`9f10a9d` still applied on top)
  produces a real merge **conflict** in 3 files (`ts-js-frontend-harnesskit-dogfood.md`,
  `frontend/loops.py`, `frontend/ts_js_frontend.py`) — expected and correct git behavior, not a
  safety defect: `9f10a9d` and `f5b3be9` touch overlapping content, so reverting the older commit
  while the newer one is still applied is genuinely ambiguous.
- **The correct rollback procedure — sequential, reverse-chronological revert — is clean:**
  `git revert --no-commit 9f10a9d` (tip first) → clean, committed as a local temp commit → `git
  revert --no-commit f5b3be9` against that state → **clean, exit 0, no conflict.**
- After the test, `git reset --hard 9f10a9daa43b107543e948a7fe0c573074d02e07` restored the exact
  original HEAD — verified by direct SHA comparison (`matches_orig: YES`) — and `git status
  --short` was empty immediately after.
- `git reset --hard` to any earlier point in this branch's history remains trivially available
  regardless of the above (a reset is never a merge, so file overlap is irrelevant to it) — this
  is the simpler, always-clean rollback path if a revert-commit history isn't required.

**Conclusion: rollback is safe.** The single conflict encountered was from an out-of-order test
methodology, not a real defect in the commits themselves.

## 5. Remote state, fresh fetch, direct query

`git fetch origin` (read-only) then `git ls-remote origin`:

```
3953f8b0c31d8cd3d8cf19445edb34fc203b00bc  HEAD
3953f8b0c31d8cd3d8cf19445edb34fc203b00bc  refs/heads/claude/read-and-plan-2an34e
fcd2d48aecb1749db1af0b7ce57acd1c5bff6714  refs/heads/main
```

No `art-0-integrated` ref exists on the remote (`git ls-remote origin
refs/heads/art-0-integrated` returns nothing).

### Re-check of the previously recorded force-update risk (§6 of the prior packet)

Still present, re-confirmed live, unresolved — this batch does not resolve it, only re-verifies
it:

- `git merge-base --is-ancestor 731ac89 3953f8b0...` → **not an ancestor** (exit 1). `731ac89`
  ("feat(rules): implement AR003 and AR014 (E05)", the root of this branch's own new history) is
  still not reachable from the current remote `claude/read-and-plan-2an34e`.
- `git merge-base --is-ancestor 731ac89 fcd2d48...` (remote `main`) → **also not an ancestor**
  (exit 1).
- `git merge-base --is-ancestor 9f10a9d <either remote ref>` → **not an ancestor of either**
  (exit 1 both) — our tip is not reachable from anything currently on the remote.

**This risk is specific to the branch name `claude/read-and-plan-2an34e`** (and to treating
`main`'s new content as this branch's base) — it does **not** block a push under a **new** branch
name. Since `art-0-integrated` has zero presence on the remote today, pushing it as a brand-new
branch cannot overwrite, diverge from, or interact with either `claude/read-and-plan-2an34e` or
`main` in any way — it is mechanically identical in shape to the HarnessKit first push (new branch
onto a remote that doesn't yet have that ref), just onto a non-empty repo instead of an empty one.

## 6. Push-safety conclusion

- **Planned operation** (not yet executed): push local `art-0-integrated` (`9f10a9d`) to
  `origin` as a **new branch**. This is provably a new-branch push, not a fast-forward of any
  existing ref and not a force update of anything — no existing remote ref shares this name.
- **No force push or force ref update is required or was used anywhere in this verification.**
- **Still open, still requires Omer's explicit decision before pushing** (unchanged from the
  prior packet's §6/§7): whether `731ac89`'s removal from `claude/read-and-plan-2an34e` was
  intentional upstream, and whether `main` is the actual long-term target branch for this
  repository going forward. This packet does not answer that question and does not need to in
  order to certify the `art-0-integrated`-as-new-branch push is safe — those are independent
  questions (this push touches nothing the divergence affects), but the underlying repository
  reorganization it points to is still worth Omer's attention separately.
- This task's own instruction did not name a specific target remote branch name for ART (unlike
  the HarnessKit push approval, which named `origin/hk/phase-a-v1-integration` explicitly) — an
  actual push command should wait for that explicit naming, not assume `art-0-integrated` is the
  intended remote name by default.

## 7. Explicitly not done in preparing this packet

No push, no tag, no merge to `main`, no `--force`/`--force-with-lease`, no history rewrite, no
HarnessKit file touched (checked: this batch's only writes are this new file and this sentence's
own existence — `git status --short` in every other worktree/repo involved stayed empty
throughout), no dirty main ART checkout touched beyond its pre-existing state, no other ART branch
touched.
