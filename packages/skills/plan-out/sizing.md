# Work sizing

Use milestones when at least two signals apply: more than six likely PR phases, roughly 25 tasks, three major subsystems, independently shippable capabilities, significant discovery dependencies, or separate rollout/migration gates. These estimates guide decomposition, not promises about future work.

A phase normally contains 2–7 tasks, changes 150–800 substantive lines across at most about 15 implementation files, takes 30–60 minutes of focused review and crosses at most one major architecture/migration boundary. It must leave a coherent mergeable outcome.

A task normally changes 1–5 related implementation files and 25–250 substantive lines, takes 5–15 minutes to review, and has a specific acceptance check. Tiny legitimate changes need not be padded to meet a lower bound. Generated files, lockfiles, snapshots, fixtures and formatting are excluded from size counts.

If a task or phase exceeds two guardrails, split it unless the split creates an invalid intermediate state; record that exception. Estimate risk as well as size: permissions, data migrations and concurrency can make a short diff a large review. Keep tests with the behavior they verify. Mark tasks needing a human decision or unavailable credential, instead of treating every task as autonomously executable.
