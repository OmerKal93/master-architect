from tenacity import retry, wait_fixed


@retry(wait=wait_fixed(1))
def charge_customer(order_id):
    return stripe_charge(order_id)
