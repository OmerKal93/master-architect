def spin():
    # An unconditional loop that does nothing agentic (no call inside it at all) -- excluded
    # from Agent recognition entirely per the frontend's heuristic, not flagged as a false
    # positive that AR001 then has to filter out. See docs/architecture/what-the-analyzer-sees.md.
    while True:
        pass
