# `client.payments.charges.create` is not in AR003's allowlist -- the frontend cannot statically
# know what `client` is bound to, so this deliberately produces no finding even though there is
# no timeout= kwarg. Silence, not a guess. See docs.md "What this rule looks for (and doesn't)".
def charge_customer(client, order_id):
    return client.payments.charges.create(order_id)
