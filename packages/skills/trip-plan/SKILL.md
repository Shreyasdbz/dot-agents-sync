---
name: trip-plan
description: "Compatibility entrypoint for Travel Planner. Use the travel-planner agent for itinerary planning; this alias preserves existing selections."
---

# Trip Plan compatibility entrypoint

The planning workflow now belongs to the selected Travel Planner agent. Consult its selected role reference for the requested itinerary work, passing only necessary authorized context. Use native delegation when available and permitted; otherwise apply the role inline and say that no separate agent ran.

Use the selected itinerary template when a written plan is requested. Do not run a second independent planning workflow here. Planning never authorizes bookings, cancellations, payments, points transfers or sharing. New configurations should select agent.travel-planner; this small alias keeps existing skill.trip-plan selections resolvable.
