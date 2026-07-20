// Inspired by (not copied from) a real HarnessKit shape: a deadline-bounded poll loop. Not even
// a candidate agent loop under this frontend's heuristic (the loop condition is not literally
// `true`/`1`), which is the correct, honest outcome for a genuinely time-bounded loop -- distinct
// from "candidate loop, proven bounded via counter-check" (see while_true_with_bound.js).
function pollUntilDone(dispatcher, dispatchId, deadlineMs) {
  while (Date.now() < deadlineMs) {
    const status = dispatcher.monitorDispatch(dispatchId);
    if (status.terminal) {
      return status;
    }
  }
  return { terminal: false, timed_out: true };
}
