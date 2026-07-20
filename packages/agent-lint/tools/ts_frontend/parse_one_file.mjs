#!/usr/bin/env node
// Real, non-executing TypeScript/JavaScript AST frontend for agent-lint's AR001/AR003/AR014
// parity slice. Uses the REAL TypeScript compiler API (`ts.createSourceFile`) to build a syntax
// tree -- this never runs, imports, or transpiles-to-executable-output the scanned source; it
// only parses (mirrors src/agent_reliability/lint/frontend/ast_utils.py's own "ast.parse only
// builds a tree, never executes" contract for Python).
//
// Contract with the Python caller (src/agent_reliability/lint/frontend/ts_js_frontend.py):
//   argv: [scriptKind ('ts'|'js'), maxAstNodes]
//   stdin: the full source text (Python reads the file, applies its own size check, then pipes
//          the text here -- this script never opens the file itself)
//   stdout: one JSON object -- { ok: true, agents, tool_calls, retry_policies, node_count } |
//           { ok: false, error_kind, message, line }
//
// Detection mirrors the Python frontend's own three passes (loops.py, calls.py, retries.py)
// exactly where the concept is language-neutral, and documents each place a JS/TS-specific
// allowlist/idiom was necessarily added (e.g. `for(;;)` as a JS-idiomatic sibling of
// `while(true)`, since JS has no `while 1:` equivalent but commonly spells "infinite loop" the
// `for(;;)` way) -- these are the SAME rule concepts (AR001/AR003/AR014), not new rules.
import * as ts from 'typescript';
import { createHash } from 'node:crypto';
import * as readline from 'node:readline';

// argv[0] is either 'ts'/'js' (single-shot mode, unchanged contract) or '--serve' (server mode,
// see runServer() below). argv[1] is maxAstNodes in both modes.
const [modeArg, maxAstNodesArg] = process.argv.slice(2);
const SERVE_MODE = modeArg === '--serve';
const scriptKindArg = modeArg;
const MAX_AST_NODES = Number(maxAstNodesArg) || 200000;

function readStdin() {
  return new Promise((resolve, reject) => {
    let data = '';
    process.stdin.setEncoding('utf8');
    process.stdin.on('data', (chunk) => { data += chunk; });
    process.stdin.on('end', () => resolve(data));
    process.stdin.on('error', reject);
  });
}

function scriptKindFor(arg) {
  return arg === 'ts' ? ts.ScriptKind.TS : ts.ScriptKind.JS;
}

// ---- structural hash: shape only, no positions (mirrors ast_utils.py#structural_hash) --------
function shapeOf(node) {
  const kind = ts.SyntaxKind[node.kind];
  const out = { kind };
  if (ts.isIdentifier(node)) out.text = node.text;
  if (ts.isLiteralExpression(node) || ts.isNumericLiteral(node) || ts.isStringLiteral(node)) {
    out.text = node.text;
  }
  if (node.kind === ts.SyntaxKind.TrueKeyword) out.text = 'true';
  if (node.kind === ts.SyntaxKind.FalseKeyword) out.text = 'false';
  const children = [];
  node.forEachChild((child) => { children.push(shapeOf(child)); });
  if (children.length) out.children = children;
  return out;
}

function structuralHash(node) {
  const shape = JSON.stringify(shapeOf(node));
  return createHash('sha256').update(shape, 'utf8').digest('hex');
}

// ---- span (mirrors ast_utils.py#span_of; Python lineno is 1-indexed, TS character/line 0-indexed) --
function spanOf(sourceFile, node) {
  const start = sourceFile.getLineAndCharacterOfPosition(node.getStart(sourceFile));
  const end = sourceFile.getLineAndCharacterOfPosition(node.getEnd());
  return {
    start_line: start.line + 1,
    start_col: start.character,
    end_line: end.line + 1,
    end_col: end.character,
  };
}

// ---- dotted name (mirrors ast_utils.py#dotted_name) --------------------------------------------
// Returns null for callees that aren't a simple identifier/property-access chain (e.g. the
// result of another call, an element-access) -- same "no guess, silence" contract as Python.
function dottedName(expr) {
  const parts = [];
  let current = expr;
  for (;;) {
    if (ts.isPropertyAccessExpression(current)) {
      parts.push(current.name.text);
      current = current.expression;
    } else if (ts.isIdentifier(current)) {
      parts.push(current.text);
      break;
    } else {
      return null;
    }
  }
  return parts.reverse().join('.');
}

// ---- node-count guard (mirrors ast_utils.py#exceeds_node_limit) --------------------------------
function countNodesBounded(root, limit) {
  let count = 0;
  let exceeded = false;
  function visit(node) {
    if (exceeded) return;
    count += 1;
    if (count > limit) { exceeded = true; return; }
    node.forEachChild(visit);
  }
  visit(root);
  return { count, exceeded };
}

// ---- AR001: unbounded agent loop --------------------------------------------------------------
// while(true) / while(1), AND for(;;) (JS-idiomatic sibling of Python's while-True -- same
// "unconditional loop" concept, a different common spelling; not a new rule/pattern class).
function isUnconditionalWhile(node) {
  const test = node.expression;
  if (test.kind === ts.SyntaxKind.TrueKeyword) return true;
  if (ts.isNumericLiteral(test) && test.text === '1') return true;
  return false;
}

function isInfiniteFor(node) {
  // for(;;) -- no condition at all is JS's other common "loop forever" idiom.
  return node.condition === undefined;
}

function containsCall(node) {
  let found = false;
  function visit(n) {
    if (found) return;
    if (ts.isCallExpression(n)) { found = true; return; }
    n.forEachChild(visit);
  }
  node.forEachChild(visit);
  return found;
}

const BOUND_BINARY_OPERATORS = new Set([
  ts.SyntaxKind.GreaterThanEqualsToken,
  ts.SyntaxKind.GreaterThanToken,
  ts.SyntaxKind.EqualsEqualsToken,
  ts.SyntaxKind.EqualsEqualsEqualsToken,
]);

// Widened from an exact top-level BinaryExpression match: a compound condition such as
// `!isContendedLockError(e) || Date.now() >= deadline` (a `||`-BinaryExpression wrapping the
// real comparison) is just as much a visible bound as a bare `x >= MAX` -- the comparison is
// still statically present, only nested one level deeper. Mirrors the same fix in loops.py
// (`_test_contains_bound_comparison`) -- confirmed false positive against real HarnessKit code
// (scripts/review-independence/run-json-atomic.js's retryOnContention) found via dogfood review.
function testContainsBoundComparison(test) {
  let found = false;
  function visit(n) {
    if (found) return;
    if (ts.isBinaryExpression(n) && BOUND_BINARY_OPERATORS.has(n.operatorToken.kind)) {
      found = true;
      return;
    }
    n.forEachChild(visit);
  }
  visit(test);
  return found;
}

function hasVisibleStepBound(bodyNode) {
  let found = false;
  function visit(n) {
    if (found) return;
    if (ts.isIfStatement(n)) {
      const test = n.expression;
      if (testContainsBoundComparison(test)) {
        let hasExit = false;
        (function walkExit(x) {
          if (hasExit) return;
          // `throw` (mirrors Python `raise`) is a valid loop exit alongside `break`/`return`:
          // it propagates out of the loop exactly as those do. Same dogfood finding as above --
          // the confirmed false positive's exit was `throw e`, not `break`/`return`.
          if (ts.isBreakStatement(x) || ts.isReturnStatement(x) || ts.isThrowStatement(x)) { hasExit = true; return; }
          x.forEachChild(walkExit);
        })(n.thenStatement);
        if (hasExit) { found = true; return; }
      }
    }
    n.forEachChild(visit);
  }
  bodyNode.forEachChild(visit);
  return found ? { hasBound: true, source: 'counter-check' } : { hasBound: false, source: null };
}

function calleeNameOfCall(callExpr) {
  const expr = callExpr.expression;
  if (ts.isIdentifier(expr)) return expr.text;
  return dottedName(expr);
}

function functionCallsItself(fn, name) {
  let found = false;
  function visit(n) {
    if (found) return;
    if (ts.isCallExpression(n) && calleeNameOfCall(n) === name) { found = true; return; }
    n.forEachChild(visit);
  }
  if (fn.body) fn.body.forEachChild(visit);
  return found;
}

function detectAgents(sourceFile) {
  const agents = [];
  function visit(node) {
    if (ts.isWhileStatement(node) && isUnconditionalWhile(node)) {
      if (containsCall(node.statement)) {
        const { hasBound, source } = hasVisibleStepBound(node.statement);
        agents.push({
          span: spanOf(sourceFile, node),
          name: null,
          has_step_bound: hasBound,
          step_bound_source: source,
          structural_hash: structuralHash(node),
        });
      }
    } else if (ts.isForStatement(node) && isInfiniteFor(node)) {
      if (containsCall(node.statement)) {
        const { hasBound, source } = hasVisibleStepBound(node.statement);
        agents.push({
          span: spanOf(sourceFile, node),
          name: null,
          has_step_bound: hasBound,
          step_bound_source: source,
          structural_hash: structuralHash(node),
        });
      }
    } else if (
      (ts.isFunctionDeclaration(node) || ts.isFunctionExpression(node)) &&
      node.name &&
      functionCallsItself(node, node.name.text)
    ) {
      const { hasBound, source } = node.body
        ? hasVisibleStepBound(node.body)
        : { hasBound: false, source: null };
      agents.push({
        span: spanOf(sourceFile, node),
        name: node.name.text,
        has_step_bound: hasBound,
        step_bound_source: source,
        structural_hash: structuralHash(node),
      });
    }
    node.forEachChild(visit);
  }
  visit(sourceFile);
  return agents;
}

// ---- AR003: tool/external call without timeout -------------------------------------------------
// Only property-access call shapes are recorded (obj.method(...)), matching calls.py's own
// "attribute-chain calls only" scope exactly -- a bare call (e.g. plain `fetch(...)`) is a known,
// documented limitation here too, not silently different from the Python frontend's own stated
// trade-off (which excludes bare `chat(...)` the same way).
function extractTimeoutFromArgs(callExpr) {
  for (const arg of callExpr.arguments) {
    if (!ts.isObjectLiteralExpression(arg)) continue;
    for (const prop of arg.properties) {
      if (!ts.isPropertyAssignment(prop)) continue;
      const key = ts.isIdentifier(prop.name) ? prop.name.text : (ts.isStringLiteral(prop.name) ? prop.name.text : null);
      if (key !== 'timeout') continue;
      const value = prop.initializer;
      if (value.kind === ts.SyntaxKind.NullKeyword) {
        return { present: true, seconds: null, explicit_none: true };
      }
      if (ts.isNumericLiteral(value)) {
        return { present: true, seconds: Number(value.text), explicit_none: false };
      }
      return { present: true, seconds: null, explicit_none: false };
    }
  }
  return { present: false, seconds: null, explicit_none: false };
}

function detectToolCalls(sourceFile) {
  const calls = [];
  function visit(node) {
    if (ts.isCallExpression(node) && ts.isPropertyAccessExpression(node.expression)) {
      const callee = dottedName(node.expression);
      if (callee !== null) {
        calls.push({
          span: spanOf(sourceFile, node),
          callee,
          structural_hash: structuralHash(node),
          timeout: extractTimeoutFromArgs(node),
        });
      }
    }
    node.forEachChild(visit);
  }
  visit(sourceFile);
  return calls;
}

// ---- AR014: retry policy without an upper bound -------------------------------------------------
// Manual-loop pattern ONLY (mirrors retries.py#_manual_loop_policies) -- deliberately does NOT
// attempt to recognize any JS retry library (async-retry, p-retry, axios-retry, ...): this
// frontend has no verified semantics for any of them, and guessing would violate the "silence
// over guessing" philosophy the Python frontend's tenacity/stamina handling already establishes.
// A dedicated JS-library retry-decorator pass is explicitly out of this slice's scope.
function hasTryCatch(node) {
  let found = null;
  function visit(n) {
    if (found) return;
    if (ts.isTryStatement(n) && n.catchClause) { found = n; return; }
    n.forEachChild(visit);
  }
  node.forEachChild(visit);
  return found;
}

function tryBlockHasBreak(tryStatement) {
  let found = false;
  function visit(n) {
    if (found) return;
    if (ts.isBreakStatement(n)) { found = true; return; }
    n.forEachChild(visit);
  }
  tryStatement.tryBlock.forEachChild(visit);
  return found;
}

function literalForLoopBound(forStatement) {
  // for (let i = 0; i < N; i++) -- literal N on the RHS of a < / <= comparison against the
  // loop variable. Anything else (a variable bound, a different shape) is not detected --
  // silence, not a guess, mirroring retries.py's own range(N)-literal-only scope.
  const cond = forStatement.condition;
  if (!cond || !ts.isBinaryExpression(cond)) return null;
  if (
    cond.operatorToken.kind !== ts.SyntaxKind.LessThanToken &&
    cond.operatorToken.kind !== ts.SyntaxKind.LessThanEqualsToken
  ) {
    return null;
  }
  if (!ts.isNumericLiteral(cond.right)) return null;
  const n = Number(cond.right.text);
  return cond.operatorToken.kind === ts.SyntaxKind.LessThanEqualsToken ? n + 1 : n;
}

function detectRetryPolicies(sourceFile) {
  const policies = [];
  function visit(node) {
    if (ts.isForStatement(node)) {
      const literal = literalForLoopBound(node);
      if (literal !== null && hasTryCatch(node.statement)) {
        policies.push({
          span: spanOf(sourceFile, node),
          bound: 'bounded',
          source: 'manual-loop',
          structural_hash: structuralHash(node),
          max_attempts: literal,
        });
      } else if (isInfiniteFor(node)) {
        // for(;;) is the same "unconditional loop" concept as while(true) here too (mirrors
        // the AR001 for(;;)/while(true) parity above) -- an unbounded manual retry loop spelled
        // either way must be classified the same. Found via independent review (this branch was
        // originally unreachable for any for-statement, since the literal-bound check above
        // always ran first and for(;;) has no condition to match against, so a
        // for(;;)-spelled retry loop silently produced zero AR014 findings).
        const tryStatement = hasTryCatch(node.statement);
        if (tryStatement && tryBlockHasBreak(tryStatement)) {
          policies.push({
            span: spanOf(sourceFile, node),
            bound: 'unbounded',
            source: 'manual-loop',
            structural_hash: structuralHash(node),
            max_attempts: null,
          });
        }
      }
    } else if (ts.isWhileStatement(node) && isUnconditionalWhile(node)) {
      const tryStatement = hasTryCatch(node.statement);
      if (tryStatement && tryBlockHasBreak(tryStatement)) {
        policies.push({
          span: spanOf(sourceFile, node),
          bound: 'unbounded',
          source: 'manual-loop',
          structural_hash: structuralHash(node),
          max_attempts: null,
        });
      }
    }
    node.forEachChild(visit);
  }
  visit(sourceFile);
  return policies;
}

// Parses one source string and returns the result object (never writes to stdout itself) --
// shared by both single-shot mode and server mode below, so the two modes can never drift in
// what they actually detect.
async function parseOne(source, forScriptKindArg) {
  const scriptKind = scriptKindFor(forScriptKindArg);

  let sourceFile;
  try {
    sourceFile = ts.createSourceFile(
      'input' + (forScriptKindArg === 'ts' ? '.ts' : '.js'),
      source,
      ts.ScriptTarget.ES2022,
      /* setParentNodes */ true,
      scriptKind
    );
  } catch (e) {
    return { ok: false, error_kind: 'parse_error', message: String(e && e.message || e), line: null };
  }

  // ts.createSourceFile does not throw on most malformed input (it produces a best-effort tree
  // with parseDiagnostics attached) -- surface real syntax errors explicitly rather than silently
  // scanning a partial/wrong tree.
  const parseDiagnostics = sourceFile.parseDiagnostics || [];
  if (parseDiagnostics.length > 0) {
    const first = parseDiagnostics[0];
    const pos = typeof first.start === 'number' ? sourceFile.getLineAndCharacterOfPosition(first.start) : null;
    return {
      ok: false,
      error_kind: 'parse_error',
      message: ts.flattenDiagnosticMessageText(first.messageText, '\n'),
      line: pos ? pos.line + 1 : null,
    };
  }

  const { count, exceeded } = countNodesBounded(sourceFile, MAX_AST_NODES);
  if (exceeded) {
    return { ok: false, error_kind: 'node_limit_exceeded', message: `AST node count exceeds limit (${MAX_AST_NODES})`, line: null };
  }

  return {
    ok: true,
    node_count: count,
    agents: detectAgents(sourceFile),
    tool_calls: detectToolCalls(sourceFile),
    retry_policies: detectRetryPolicies(sourceFile),
  };
}

// Single-shot mode: EXACT same contract as before this file supported server mode -- argv[0] is
// 'ts'/'js', stdin is the raw source text, stdout gets exactly one JSON object, process exits.
// Kept unchanged so every existing caller/test that spawns this script per file still works.
async function runSingleShot() {
  const source = await readStdin();
  const result = await parseOne(source, scriptKindArg);
  process.stdout.write(JSON.stringify(result));
}

// Server mode (additive, opt-in via argv[0] === '--serve'): amortizes Node process startup +
// `require('typescript')` module-load cost (measured ~290ms/file in single-shot mode, dominated
// by startup, not actual parsing) across an entire scan instead of paying it once per file --
// this is what made a full HarnessKit-repo scan hit the whole-scan wall-clock budget from spawn
// overhead alone (see docs/ts-js-frontend-harnesskit-dogfood.md, F6). Wire protocol: the caller
// (ts_js_frontend.py's persistent worker) writes one newline-delimited JSON request
// {id, script_kind, source} per file to this process's stdin and reads one newline-delimited
// JSON response {id, ...same shape parseOne() always returned...} per line from stdout. This
// process stays alive, reusing its already-loaded `typescript` module, until the caller closes
// stdin (clean EOF exit) or kills it (e.g. after a per-file timeout on the Python side). Detection
// logic is identical to single-shot mode -- parseOne() is the single source of truth for both.
async function runServer() {
  const rl = readline.createInterface({ input: process.stdin, crlfDelay: Infinity });
  for await (const line of rl) {
    if (!line.trim()) continue;
    let request;
    try {
      request = JSON.parse(line);
    } catch (e) {
      process.stdout.write(
        JSON.stringify({ id: null, ok: false, error_kind: 'internal_error', message: `malformed request: ${String(e && e.message || e)}`, line: null }) + '\n'
      );
      continue;
    }
    let result;
    try {
      result = await parseOne(request.source, request.script_kind);
    } catch (e) {
      result = { ok: false, error_kind: 'internal_error', message: String(e && e.stack || e), line: null };
    }
    result.id = request.id;
    process.stdout.write(JSON.stringify(result) + '\n');
  }
}

if (SERVE_MODE) {
  runServer().catch((e) => {
    process.stdout.write(
      JSON.stringify({ id: null, ok: false, error_kind: 'internal_error', message: String(e && e.stack || e), line: null }) + '\n'
    );
    process.exitCode = 1;
  });
} else {
  runSingleShot().catch((e) => {
    process.stdout.write(JSON.stringify({ ok: false, error_kind: 'internal_error', message: String(e && e.stack || e), line: null }));
  });
}
