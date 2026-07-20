function stepAgent(depth) {
  if (depth >= 10) {
    return;
  }
  stepAgent(depth + 1);
}
