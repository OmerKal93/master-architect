from tenacity import retry, wait_fixed


@retry(wait=wait_fixed(2))
def call_flaky_service():
    return do_work()
