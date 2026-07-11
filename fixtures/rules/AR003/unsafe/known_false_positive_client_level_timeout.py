def ask_model(prompt):
    # KNOWN FALSE POSITIVE (see docs.md "Known limitation: client/session-level timeout
    # configuration is not recognized"): this client genuinely has a real 30-second timeout
    # configured, but AR003 has no way to see it -- it only reads the timeout= keyword at the
    # call site itself, never a client's construction-time configuration. This fixture exists to
    # make that documented gap visible and testable, not to claim the code below is unsafe.
    client = OpenAI(timeout=30)
    return client.chat.completions.create(model="gpt-4", messages=[{"role": "user", "content": prompt}])
