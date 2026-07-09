import requests


def charge_customer(order_id):
    return requests.post("https://api.example.invalid/charge", timeout=30)
