function askModel(client, prompt) {
  return client.messages.create({ model: "claude-sonnet-5", messages: [{ role: "user", content: prompt }] });
}
