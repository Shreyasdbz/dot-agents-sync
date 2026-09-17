"""In-memory implementation retained from the original prototype."""


def apply_credit(seen, balances, tenant, event, account, amount):
    """Deduplicate within one caller-owned process; this path has no persistence."""
    key = (tenant, event)
    if key not in seen:
        balances[(tenant, account)] = balances.get((tenant, account), 0) + amount
        seen.add(key)
    return balances.get((tenant, account), 0)
