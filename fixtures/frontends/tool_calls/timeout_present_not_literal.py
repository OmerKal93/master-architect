import requests

DEFAULT_TIMEOUT = 30


def charge_customer(order_id):
    return requests.post("https://api.example.invalid/charge", timeout=DEFAULT_TIMEOUT)
