from tenacity import retry


# Unqualified `retry()` with no disambiguating kwargs (no stop=/wait=/reraise=/attempts=) is
# ambiguous between tenacity, stamina, and an unrelated local decorator of the same name.
# Deliberately not recognized (silence over guessing) -- same reasoning as the bare no-call form.
@retry()
def call_flaky_service():
    return do_work()
