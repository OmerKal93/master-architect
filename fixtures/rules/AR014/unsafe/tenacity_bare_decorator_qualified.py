import tenacity


@tenacity.retry
def call_flaky_service():
    return do_work()
