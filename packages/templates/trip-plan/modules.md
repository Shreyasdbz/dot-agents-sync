# Travel data modules

## Groups and occupancy

Record stable group IDs, traveler counts, separate arrivals/departures and shared segments. Map each group to lodging for each night. For hotels track room type/count and occupants; for apartments/rentals track units, bedrooms, beds and capacity; for family stays track host confirmation and sleeping space. Do not treat a bedroom as a room booking or multiply a shared property charge by traveler count. Flag accommodation gaps rather than assuming everyone follows the same route.

## Transport leg

Record mode, origin/destination, local departure and arrival dates/times with zones or UTC offsets, overnight/day-change marker, verified duration, status, baggage/accessibility constraints, connection buffer and source/check time. A route drawing supplements this text; it is not navigation or a live flight track. Do not calculate elapsed time by subtracting wall-clock labels in different zones.

## Cost ledger

| Category | Quantity / basis | Currency | Amount | Status | Included / excluded | Source / checked |
| --- | --- | --- | --- | --- | --- | --- |

Use integer minor units for software calculations. Show separate subtotals per currency unless an explicit exchange rate, date and rounding rule are supplied. Label incomplete totals as known-category subtotals. Separate paid, remaining, optional and contingency figures; do not add a subtotal to its own component rows.

## Place / booking card

Keep name/area, candidate or confirmed status, relevant dates, useful public directions, access requirements and current cancellation/payment conditions only when verified. Private booking references, personal contact details and room numbers belong in authorized private context, not hidden HTML.

## Source and decision record

Retain claim, source link, observed date, applicable travel date and unresolved constraint. Group equivalent repeated checks rather than repeating a citation on every line. A screenshot without a date or current lookup is provisional.
