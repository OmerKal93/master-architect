def charge_until_success(order_id):
    while True:
        try:
            result = stripe_charge(order_id)
            break
        except TransientError:
            continue
    return result
