def run_batch(client, items):
    for item in items:
        client.process(item)
