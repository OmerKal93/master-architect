function runAgent(client) {
  for (let i = 0; i < 25; i++) {
    client.step();
  }
}
