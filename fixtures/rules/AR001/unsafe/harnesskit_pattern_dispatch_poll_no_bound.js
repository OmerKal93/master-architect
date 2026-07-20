// Inspired by (not copied from) a real HarnessKit shape: a naive dispatch-status poll loop with
// no step/time bound at all -- the buggy version of the pattern in
// safe/harnesskit_pattern_dispatch_poll_with_deadline.js.
function pollUntilDone(dispatcher, dispatchId) {
  while (true) {
    const status = dispatcher.monitorDispatch(dispatchId);
    if (status.terminal) {
      return status;
    }
  }
}
