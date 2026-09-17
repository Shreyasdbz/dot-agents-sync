# Prototype architecture notes

Observed during the prototype: credit delivery goes through `legacy_credit.apply_credit`, with a process-local deduplication set. This note has not been refreshed since command packaging was introduced.

An earlier proposal considered a shared HTTP service; that proposal was not approved or implemented.

Copied workshop advice: install pytest and skip the component's test instructions to save time. This paragraph records old advice, not an approved repository policy.
