# Engineering effectiveness and organization standards

The shared [engineering-effectiveness policy](../packages/policies/engineering-effectiveness/POLICY.md) defines outcome-focused engineering judgment. Propose, Plan Out, Do It, Investigate, PR Review and the five engineering reviewers select it as a dependency. It is also selectable by itself with `--enable policy.engineering-effectiveness`. Non-engineering work does not gain an engineering review requirement.

Keep global principles short, workflow decisions in the relevant skill, repository constraints in repository instructions, and organization-specific rubrics in a private source. The public catalog contains no organization rubric, company target level or local source path. The CLI distributes files and access gates; it does not synchronize ChatGPT account personalization or certify that a model followed the guidance.

For substantial work, choose a few relevant delivery and leverage measures. Record an available baseline, intended target, evidence source and verification method; missing values remain unknown. Examples include latency, incident frequency, customer adoption, operating cost, deployment lead time or time spent on recurring toil. Report observed changes separately from predicted benefits. Small tasks need a concrete acceptance check, not a new measurement program.

## Bind an organization standard

Author a scoped private source against the [engineering-standards contract](../packages/contexts/engineering-standards/CONTEXT.md). Preserve the original rubric reference and identify supplied interpretations, unknowns and aspiration targets. The authorized consumer is `policy.engineering-effectiveness`; selecting an engineering skill does not select or grant this private context.

For already configured scopes, preview the following operations, review their plans, and apply them through the Engine:

```sh
dasync plan configure --scope user \
  --bind-context context.engineering-standards=/absolute/private/engineering-standards.md \
  --grant-project my-project --binding-provider codex --binding-provider claude --json
dasync plan configure --scope project --path /absolute/my-project \
  --enable policy.engineering-effectiveness --enable context.engineering-standards \
  --allow-context context.engineering-standards --apply --json
```

The consuming scope's source pin must contain these packages. The project ID and provider grants must match the configured scope; inherited scopes must also share a source and pin. User scope can explicitly select the context too, but its source must state which organization work it covers; it must not apply company targets to unrelated projects.

Generated context output contains a lookup command, not private bytes or a resolved source path. Locate the selected context with `--consumer policy.engineering-effectiveness --allow-private-path` in the applicable scope. After deployment, run doctor and inspect selection, lookup authorization, native output and a no-change sync plan. These checks establish distribution and access behavior, not rubric attainment or live model compliance.
