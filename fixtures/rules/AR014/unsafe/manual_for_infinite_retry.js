// Regression fixture (found via independent review): the same unbounded manual-retry shape as
// manual_while_true_retry.js, spelled with for(;;) instead of while(true) -- both are the same
// "unconditional loop" concept for AR001/AR014 and must be detected identically.
function uploadWithRetry(client, path) {
  for (;;) {
    try {
      client.upload(path);
      break;
    } catch (err) {
      continue;
    }
  }
}
