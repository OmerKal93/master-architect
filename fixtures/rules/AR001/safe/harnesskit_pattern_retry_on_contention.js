// Regression fixture (found via independent dogfood review against real HarnessKit code):
// scripts/review-independence/run-json-atomic.js's retryOnContention() was a confirmed false
// positive. A for(;;) retry loop whose bound is a compound condition
// (`!isContendedLockError(e) || Date.now() >= deadline`) exiting via `throw`, not a bare
// `if <comparison>: break/return`. Proves the widened has_step_bound heuristic
// (testContainsBoundComparison + throw-as-exit) now recognizes it as bounded.
function retryOnContention(fn, deadline) {
  for (;;) {
    try {
      return fn();
    } catch (e) {
      if (!isContendedLockError(e) || Date.now() >= deadline) throw e;
      sleepSync(50);
    }
  }
}
