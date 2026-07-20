function runAgent(client) {
  let stepCount = 0;
  while (true) {
    client.step();
    stepCount += 1;
    if (stepCount >= 25) {
      break;
    }
  }
}
