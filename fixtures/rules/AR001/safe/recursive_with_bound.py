def run_agent(client, depth=0):
    if depth >= 25:
        return
    client.step()
    run_agent(client, depth + 1)
