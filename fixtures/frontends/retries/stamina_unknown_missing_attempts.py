import stamina


@stamina.retry(timeout=30)
def charge_customer(order_id):
    return stripe_charge(order_id)
