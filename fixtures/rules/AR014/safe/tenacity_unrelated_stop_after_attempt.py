import myproject
from tenacity import retry


@retry(stop=myproject.stop_after_attempt(3))
def call_flaky_service():
    return do_work()
