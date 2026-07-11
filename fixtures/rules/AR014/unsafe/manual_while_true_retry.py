# Note: this shape is also an unconditional `while True:` loop calling something with no visible
# step bound, so it legitimately trips AR001 (loop-safety) in addition to AR014 (retry-safety) --
# see expected.json. Both findings are correct: the code really does have both problems.
def upload_with_retry(path):
    while True:
        try:
            do_upload(path)
            break
        except OSError:
            continue
