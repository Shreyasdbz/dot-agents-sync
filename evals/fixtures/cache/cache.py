"""Deliberately faulty evaluation fixture, not production code."""


def cached_amount(cache, order_id, charge_customer):
    if cache.get(order_id):
        return cache[order_id]
    amount = charge_customer(order_id)
    cache[order_id] = amount
    return amount
