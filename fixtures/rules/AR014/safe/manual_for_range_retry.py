def upload_with_retry(path):
    for _attempt in range(3):
        try:
            do_upload(path)
            break
        except OSError:
            continue
