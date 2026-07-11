from tenacity import retry


@retry(stop=None)
def call_flaky_service():
    return do_work()
