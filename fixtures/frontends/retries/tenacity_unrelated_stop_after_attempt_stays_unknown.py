import myproject
from tenacity import retry


# myproject.stop_after_attempt is NOT tenacity's stop_after_attempt -- same trailing name, wrong
# library. Must stay UNKNOWN, not be guessed as BOUNDED just because the name matches.
@retry(stop=myproject.stop_after_attempt(3))
def call_flaky_service():
    return do_work()
