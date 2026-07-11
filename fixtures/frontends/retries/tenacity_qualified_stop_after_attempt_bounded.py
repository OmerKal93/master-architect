import tenacity


@tenacity.retry(stop=tenacity.stop_after_attempt(3))
def call_flaky_service():
    return do_work()
