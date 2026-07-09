from tenacity import retry, stop_after_attempt


@retry(stop=stop_after_attempt(3))
def charge_customer(order_id):
    return stripe_charge(order_id)
