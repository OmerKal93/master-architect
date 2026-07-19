#!/usr/bin/env node
// ART-0 Target 1 (AO-1 mutation dogfood) -- the single APPROVED mutant.
//
// Standalone reimplementation, NOT a copy of or edit to HarnessKit's real
// scripts/manager-advisor/ao1-dispatch.js -- that file is never touched. This models the bug
// ART-0-plan.md section 5 approved: the real claimDecisionDispatch has TWO independent dedup
// layers (config/ao1-dispatch-policy.json's own decision_dispatch_registry_dir comment names both
// explicitly): (1) an `if (existing) return fail(...)` pre-check via readJson, AND (2) writing
// with the OS-level exclusive-create flag `{ flag: 'wx' }`, which throws EEXIST on a second write
// regardless of (1).
//
// CORRECTED (independent review): an earlier version of this comment claimed only the `if`
// pre-check (1) was removed. A reviewer proved that framing was incomplete -- removing ONLY (1)
// while keeping a `{flag:'wx'}` write would still throw EEXIST on the second attempt and still be
// caught as a duplicate, defeating the mutant's purpose. This mutant genuinely removes BOTH
// layers: no existing-file check, AND a plain `fs.writeFileSync(p, ...)` with no `flag` option
// (default 'w', silently overwrites) -- this is the real, complete diff needed to reproduce the
// bug the mutation-testing dogfood target requires (ART-0-plan.md section 7, "real diff of the
// single AO-1 mutant").
'use strict';
const path = require('path');
const fs = require('fs');

const outLogPath = process.argv[2];
const scratchRoot = process.argv[3];

function mutantClaimDecisionDispatch({ decisionId, dispatchId, root }) {
  const dir = path.join(root, 'dispatches', '.ao1-decision-map');
  fs.mkdirSync(dir, { recursive: true });
  const p = path.join(dir, `${decisionId}.json`);
  // BUG (the approved mutant): no existing-claim check before writing -- the real
  // claimDecisionDispatch's `if (existing) return fail(...)` guard is simply absent here.
  fs.writeFileSync(p, JSON.stringify({ decision_id: decisionId, dispatch_id: dispatchId, claimed_at: new Date().toISOString() }, null, 2));
  return { ok: true };
}

fs.mkdirSync(scratchRoot, { recursive: true });

const decisionId = 'art0-mutant-dedup-check';
const attempts = [
  mutantClaimDecisionDispatch({ decisionId, dispatchId: 'dispatch-attempt-1', root: scratchRoot }),
  mutantClaimDecisionDispatch({ decisionId, dispatchId: 'dispatch-attempt-2', root: scratchRoot })
];

const lines = attempts.map((r, i) => JSON.stringify({
  decision_id: decisionId,
  dispatch_id: `dispatch-attempt-${i + 1}`,
  ok: r.ok === true,
  reason: r.reason || null
}));
fs.writeFileSync(outLogPath, lines.join('\n') + '\n');
console.log(JSON.stringify({ ok: true, attempts, log_path: outLogPath }));
