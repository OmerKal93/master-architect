from tenacity import retry


@retry(stop=None)
def charge_customer(order_id):
    return stripe_charge(order_id)
