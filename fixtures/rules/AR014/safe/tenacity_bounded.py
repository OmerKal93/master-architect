from tenacity import retry, stop_after_attempt


@retry(stop=stop_after_attempt(3))
def call_flaky_service():
    return do_work()
