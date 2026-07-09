import stamina


@stamina.retry(attempts=5)
def charge_customer(order_id):
    return stripe_charge(order_id)
