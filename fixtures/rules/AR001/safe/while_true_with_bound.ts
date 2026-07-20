interface AgentClient {
  step(): void;
}

function runAgent(client: AgentClient): void {
  let stepCount = 0;
  while (true) {
    client.step();
    stepCount += 1;
    if (stepCount >= 25) {
      break;
    }
  }
}
