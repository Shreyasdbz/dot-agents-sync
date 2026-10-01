---
name: trip-publish
description: "Turn an approved itinerary into a mobile-friendly HTML travel guide. Creating the file is distinct from hosting or sharing it."
---

# Trip Publish

Apply [Visual Artifacts](references/skill.visual-artifacts/SKILL.md) for the guide's hierarchy, route/timeline explanations and useful state feedback. Preserve mobile travel priorities and verified itinerary facts; do not imply live maps, availability or tracking.

Use the approved itinerary as the source of truth. Preserve dates, local times, locations, confirmed bookings and unresolved candidates. Ask about the sharing audience only when it changes what can safely appear.

Before building the page, consult the selected Travel Planner agent for a bounded content review using only the necessary itinerary and authorized traveler constraints. Use native delegation when available and permitted; otherwise load its selected role reference and perform the review inline, disclosing that no separate agent ran. Resolve material corrections with the user, then implement the agreed content; do not let this review silently reopen the trip plan. Do not pass the raw private preference file to a subagent without authorization.

Create a self-contained HTML guide from [trip.html](references/template.trip-publish/trip.html) and consult its [composition guidance](references/template.trip-publish/components.md) when adapting the page. Put the horizontal route preview at the top of At a glance. Keep any additional overview and booking cards closed by default, with dates, route or property, travelers where relevant, and booking status visible in each summary; place confirmation, address, policy and action controls inside. Do not put links or buttons inside a disclosure summary. Prioritize the day plan and movement between stops over repeated explanation before the itinerary.

Use the template's dated itinerary cards, inline SVG stop icons and connected timeline to show sequence and transport. Keep flexible times and generous travel buffers explicit. Give known addresses a visible, selectable value with an icon-only Copy control and a distinct icon-only map link where useful. Both controls need field-specific accessible names and 44px targets; map links remain links. Do not invent a lodging address or choose between conflicting tour meeting addresses before the reservation resolves them. Keep unavailable details clearly pending rather than adding dead copy controls.

Keep costs, cancellation terms and alternatives decision-useful and below the itinerary. Label prebooking quotes, actual paid amounts, conditional cashback and unbooked experiences distinctly. Support small screens, keyboard access, readable light/dark themes and printing; keep CSS/JavaScript inside the file.

Exclude booking references, identity documents, contact details and private notes from a shareable artifact unless specifically authorized and necessary. Hidden markup, scripts and comments are still disclosed content. Do not add trackers or external assets that transmit trip details.

Compare the generated content against the itinerary, then render and exercise disclosure summaries, direct links that reveal a closed card, Copy and map controls, theme, print expansion/restoration and narrow-width overflow when tools permit. Confirm that collapsed summaries contain no action controls and that icon-only controls retain accessible names. Disclose any unperformed visual or interaction checks. Changing availability belongs to Travel Planner review, not an unsourced rewrite during publishing.

Load context.artifact-routing for the HTML destination, then deliver the file. The skill's name does not grant permission to host, upload or send it; do those actions only when requested, and verify the actual published result.
