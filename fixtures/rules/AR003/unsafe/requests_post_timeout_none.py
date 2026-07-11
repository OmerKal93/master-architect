import requests


def charge_customer(order_id):
    # timeout=None disables the timeout entirely for requests -- exactly as unbounded as if the
    # keyword were never passed at all.
    return requests.post("https://api.example.invalid/charge", timeout=None)
