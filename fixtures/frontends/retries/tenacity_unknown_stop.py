from tenacity import retry

custom_stop = build_custom_stop_strategy()


@retry(stop=custom_stop, wait=wait_fixed(1))
def charge_customer(order_id):
    return stripe_charge(order_id)
