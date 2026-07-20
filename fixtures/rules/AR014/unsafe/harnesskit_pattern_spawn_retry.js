// Inspired by (not copied from) a real HarnessKit shape: a naive "keep retrying a spawn until it
// works" loop with no upper bound -- the buggy version of a real dispatcher's bounded retry.
function spawnWithRetry(dispatcher, command) {
  while (true) {
    try {
      dispatcher.spawnDispatch(command);
      break;
    } catch (err) {
      continue;
    }
  }
}
