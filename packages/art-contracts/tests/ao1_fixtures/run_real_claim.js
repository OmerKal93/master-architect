#!/usr/bin/env node
// ART-0 Target 1 (AO-1 mutation dogfood) -- REAL, UNMODIFIED case.
//
// Requires the real, already-merged claimDecisionDispatch from HarnessKit's own
// scripts/manager-advisor/ao1-dispatch.js by path -- READ-ONLY, never edits or writes to the
// HarnessKit repo. Calls it twice with the SAME decision_id against a fresh, disposable scratch
// root and appends one ndjson line per attempt {decision_id, dispatch_id, ok, reason} to the
// path given as argv[3]. This is the ground-truth "what does the real dedup guard actually do"
// case ART-0's `at_most_once` contract is checked against.
'use strict';
const path = require('path');
const fs = require('fs');

const HARNESSKIT_REPO = process.argv[2] || 'C:/Dev/hk-worktrees/phase-a-v1-integration';
const outLogPath = process.argv[3];
const scratchRoot = process.argv[4];

const { claimDecisionDispatch } = require(path.join(HARNESSKIT_REPO, 'scripts/manager-advisor/ao1-dispatch.js'));

fs.mkdirSync(scratchRoot, { recursive: true });

const decisionId = 'art0-real-dedup-check';
const attempts = [
  claimDecisionDispatch({ decisionId, dispatchId: 'dispatch-attempt-1', root: scratchRoot }),
  claimDecisionDispatch({ decisionId, dispatchId: 'dispatch-attempt-2', root: scratchRoot })
];

const lines = attempts.map((r, i) => JSON.stringify({
  decision_id: decisionId,
  dispatch_id: `dispatch-attempt-${i + 1}`,
  ok: r.ok === true,
  reason: r.reason || null
}));
fs.writeFileSync(outLogPath, lines.join('\n') + '\n');
console.log(JSON.stringify({ ok: true, attempts, log_path: outLogPath }));
