from tenacity import retry


# Unqualified retry() with no disambiguating kwargs -- ambiguous, deliberately not recognized.
@retry()
def call_flaky_service():
    return do_work()
