import requests


def charge_customer(order_id):
    return requests.post(
        "https://api.example.invalid/charge",
        json={"order_id": order_id},
        timeout=10,
    )
