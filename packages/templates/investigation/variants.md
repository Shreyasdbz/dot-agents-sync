# Investigation variants

## Incident / outage

Add a timezone-qualified timeline of first observation, detection, mitigation and recovery. Separate trigger, root cause and contributing factors. Record confirmed impact versus unknown blast radius. Include current containment and verification of recovery only when observed. An after-action report may include follow-ups, but do not create tracker items without authority.

## Correctness / regression

Add expected versus observed behavior, minimal reproduction, relevant code/data path and a discriminating test. Track hypotheses as supported/rejected/unresolved with the evidence for each. Distinguish the defect from unrelated pre-existing behavior.

## Performance / capacity

State workload, environment, sample size, measurement window, units, percentiles and baseline. Separate instrumented measurements from estimates. Account for cold/warm state, concurrency and confounders. Describe the bottleneck and the next experiment; do not extrapolate a microbenchmark to production without evidence.

## Research / feasibility

Define the decision criteria, dated primary sources, conflicting findings, applicability limits and unanswered questions. Use a comparison only across equivalent dimensions. An unavailable live source remains unverified, even when an older screenshot looks persuasive.
