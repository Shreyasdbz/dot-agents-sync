"""Validation shared by credit callers."""


def apply_credit(store, tenant, event, account, amount):
    """Apply a nonnegative integer credit for nonempty tenant-local identifiers."""
    if not all(isinstance(value, str) and value.strip() for value in (tenant, event, account)):
        raise ValueError("Tenant, event and account are required")
    if type(amount) is not int or amount < 0:
        raise ValueError("Amount must be a nonnegative integer")
    return store.apply_credit(tenant, event, account, amount)
