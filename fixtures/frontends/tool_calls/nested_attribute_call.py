def charge_customer(client, order_id):
    return client.payments.charges.create(order_id, timeout=15)
