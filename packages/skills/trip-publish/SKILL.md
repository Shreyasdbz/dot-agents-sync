---
name: trip-publish
description: "Turn an approved itinerary into a mobile-friendly HTML travel guide. Creating the file is distinct from hosting or sharing it."
---

# Trip Publish

Use the approved itinerary as the source of truth. Preserve dates, local times, locations, confirmed bookings and unresolved candidates. Ask about the sharing audience only when it changes what can safely appear.

Before building the page, consult the selected Travel Planner agent for a bounded content review using only the necessary itinerary and authorized traveler constraints. Use native delegation when available and permitted; otherwise load its selected role reference and perform the review inline, disclosing that no separate agent ran. Resolve material corrections with the user, then implement the agreed content; do not let this review silently reopen the trip plan. Do not pass the raw private preference file to a subagent without authorization.

Create a self-contained HTML guide from [trip.html](references/template.trip-publish/trip.html). Prioritize today's plan, movement between stops, usable map links and quick access to essential logistics. Support small screens, keyboard access, readable light/dark themes and printing; keep CSS/JavaScript inside the file.

Exclude booking references, identity documents, contact details and private notes from a shareable artifact unless specifically authorized and necessary. Hidden markup, scripts and comments are still disclosed content. Do not add trackers or external assets that transmit trip details.

Compare the generated content against the itinerary, then render and exercise navigation, theme controls, links and overflow when tools permit. Disclose any unperformed visual checks. Changing availability belongs to Travel Planner review, not an unsourced rewrite during publishing.

Deliver the HTML file. The skill's name does not grant permission to host, upload or send it; do those actions only when requested, and verify the actual published result.
