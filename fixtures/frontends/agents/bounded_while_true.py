def run_agent(client):
    step_count = 0
    while True:
        client.step()
        step_count += 1
        if step_count >= 10:
            break
