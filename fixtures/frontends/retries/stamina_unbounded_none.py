import stamina


@stamina.retry(attempts=None)
def charge_customer(order_id):
    return stripe_charge(order_id)
