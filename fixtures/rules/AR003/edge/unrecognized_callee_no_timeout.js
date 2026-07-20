function chargeCustomer(billing, order) {
  // Not in the recognized-call-shape allowlist -- an arbitrary in-process method call, not a
  // known HTTP/SDK client. Silence, not a guess.
  return billing.charges.create(order);
}
