def charge_with_retries(order_id):
    for attempt in range(3):
        try:
            return stripe_charge(order_id)
        except TransientError:
            continue
