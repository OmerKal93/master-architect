from tenacity import retry


# No parens, no `tenacity.` qualification -- ambiguous with stamina or an unrelated local
# `retry` decorator. Deliberately not recognized (silence over guessing).
@retry
def call_flaky_service():
    return do_work()
