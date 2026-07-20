interface AgentClient {
  step(): void;
}

function runAgent(client: AgentClient): void {
  while (true) {
    client.step();
  }
}
