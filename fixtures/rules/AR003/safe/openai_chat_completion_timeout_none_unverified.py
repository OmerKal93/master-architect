def ask_model(client, prompt):
    # timeout=None's real semantics for the OpenAI SDK are not verified the way they are for
    # requests/httpx (see docs.md) -- treated as "present, not provably absent" rather than
    # guessed to be unsafe. Deliberately not flagged.
    return client.chat.completions.create(
        model="gpt-4",
        messages=[{"role": "user", "content": prompt}],
        timeout=None,
    )
