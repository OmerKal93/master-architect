// A hand-rolled counter compared against a VARIABLE limit (not a literal) -- not detected by this
// frontend's manual-loop heuristic (retries.py's own documented limitation, mirrored here).
// Silence, not a guess: no RetryPolicy at all, so no finding from AR014.
function uploadWithRetry(client, path, maxAttempts) {
  let attempts = 0;
  while (attempts < maxAttempts) {
    try {
      client.upload(path);
      break;
    } catch (err) {
      attempts += 1;
    }
  }
}
