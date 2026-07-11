# A hand-rolled counter compared against a variable limit -- the frontend's documented, stated
# limitation (see retries.py's module docstring): not recognized as a retry construct at all, so
# no RetryPolicy is produced and this rule stays silent. Silence, not a guess.
def upload_with_retry(path, max_attempts):
    attempts = 0
    while attempts < max_attempts:
        try:
            do_upload(path)
            break
        except OSError:
            attempts += 1
