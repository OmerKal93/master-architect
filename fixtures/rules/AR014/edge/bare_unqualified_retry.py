from tenacity import retry


# No parens, no `tenacity.` qualification -- ambiguous with stamina or an unrelated local
# decorator of the same name. Deliberately not recognized (silence over guessing).
@retry
def call_flaky_service():
    return do_work()
