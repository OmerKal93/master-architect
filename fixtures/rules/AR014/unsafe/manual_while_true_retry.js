// Note: this shape is also an unconditional while(true) loop calling something with no visible
// step bound, so it legitimately trips AR001 (loop-safety) in addition to AR014 (retry-safety) --
// see expected.json. Both findings are correct: the code really does have both problems.
function uploadWithRetry(client, path) {
  while (true) {
    try {
      client.upload(path);
      break;
    } catch (err) {
      continue;
    }
  }
}
