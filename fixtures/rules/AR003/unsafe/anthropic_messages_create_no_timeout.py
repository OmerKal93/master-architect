def ask_model(client, prompt):
    return client.messages.create(
        model="claude-3-5-sonnet-latest",
        max_tokens=1024,
        messages=[{"role": "user", "content": prompt}],
    )
