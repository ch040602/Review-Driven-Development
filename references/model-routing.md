# Model routing

RDD routes subagent work from requirements, not from a role-to-model `if` chain. The bundled policy lives in `model-routing-policy.json`; `model_router.py` validates and evaluates it.

## Current model catalog

Only these models are enabled by the bundled policy:

| Model | Intended work | Complexity ceiling | Supported reasoning effort |
|---|---|---|---|
| `gpt-5.3-codex-spark` | Simple implementation and structured/local criticism | `local` | `low`, `medium` |
| `gpt-5.6` | Additional logic design, cross-file reasoning, security/data/architecture review | `architectural` | `low`, `medium`, `high`, `max` |

The catalog is configuration, not router code. Replace or extend it through `--routing-policy <path>` when the actually available models change. Use repeated `--available-model <id>` arguments to narrow one run to models confirmed available by the caller. If no availability list is supplied, the router uses only catalog entries marked `available_by_default` and reports `availability_source: catalog-default`.

## Decision pipeline

For each route, the policy supplies or derives:

1. task kind and contract (`implementation` or `critical-only`),
2. required capabilities,
3. complexity floor (`mechanical`, `local`, `cross-file`, `architectural`),
4. reasoning floor (`low`, `medium`, `high`, `max`),
5. available model IDs,
6. per-route and whole-plan budget ceilings.

The router filters out any candidate that misses a capability, complexity floor, reasoning floor, availability constraint, or budget ceiling. It then selects the lowest cost/latency candidate that satisfies every hard requirement. It never converts a requested `max` or `high` route to a weaker effort just to obtain a model.

## Default task routes

| Work | Default route |
|---|---|
| Mechanical/local implementation with known acceptance criteria | Codex Spark / `low` |
| Requirements, tests, docs, validation evidence, maintainability, simplification | Codex Spark / `medium` (`low` at minimal critic depth) |
| New logic, cross-file coupling, framework/runtime tradeoffs, reuse/refactor, performance/accuracy | GPT-5.6 / `high` |
| Security, data correctness, or architecture review | GPT-5.6 / `high` |
| The preceding risk work at explicit `critic-depth=deep` | GPT-5.6 / `max`, requiring `agent-budget=deep` |

`rdd_spark_low_critic` pins Spark/`low`, `rdd_spark_critic` pins Spark/`medium`, `rdd_standard_critic` pins GPT-5.6/`high`, and `rdd_deep_critic` pins GPT-5.6/`max`. A route exposes a custom agent name only when the static config exactly matches the selected model and effort. Otherwise the spawn surface must honor the emitted `model` and `reasoning_effort` directly; if it cannot, keep the work with the current main agent.

## Budget and fallback rules

Budget profiles are data in the policy:

- `spark-first`: choose Spark whenever it satisfies the task, allow GPT-5.6/`high` when extra logic requires it, and cap the default plan at 24 relative cost units.
- `balanced`: keep the same reasoning ceiling but allow a larger 36-unit plan.
- `deep`: permit `max` and a 64-unit plan.

`max_cost_tier`, `max_reasoning_effort`, `max_fallbacks`, and `max_plan_cost_units` may further tighten a run. Relative cost units are deterministic routing weights (`cost_tier × reasoning rank`), not token or currency estimates.

Selected routes include a bounded `fallbacks` list. Fallback candidates already satisfy the same capability, complexity, reasoning, availability, and per-route budget requirements. Whole-plan budget exhaustion clears the selected model and returns `plan_budget_exceeded` so a consumer cannot accidentally execute an over-budget route.

No valid route is explicit:

| Status | Meaning |
|---|---|
| `unsupported` | No catalog model has the required capability/complexity/reasoning combination. |
| `unavailable` | A capable catalog model exists, but it is absent from the supplied availability list. |
| `budget_limited` | A capable and available model exists, but the requested effort or cost exceeds the per-route budget. |
| `plan_budget_exceeded` | The route would exceed the spawn plan's aggregate cost-unit limit. |

In all four cases, do not spawn. Keep the work with the current main agent or explicitly expand the catalog/availability/budget. Do not silently weaken the task.

## CLI examples

```text
python scripts/model_router.py --list-models
python scripts/model_router.py --phase execution --task-kind simple-implementation
python scripts/model_router.py --phase execution --task-kind logic-design
python scripts/workflow_runner.py --root . --phase execution --implementation-task-kind simple-implementation --available-model gpt-5.3-codex-spark --available-model gpt-5.6
python scripts/model_router.py --phase preplan --role security-risk-critic --critic-depth deep --agent-budget deep
python scripts/model_router.py --phase validation --role simplification-critic --available-model gpt-5.3-codex-spark --available-model gpt-5.6
```

Generated briefs and spawn plans are scaffolds only. They do not claim that a subagent ran. Critic routes remain critical-only; implementation routes do not grant authority beyond the current user request.
