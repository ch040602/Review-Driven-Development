# Model routing

RDD does not force the main implementation agent onto Spark. It prepares custom-agent configs and spawn plans so the main agent or user can decide when extra review is worth the token cost.

| Work | Route |
|---|---|
| Requirements gaps, docs checks, validation evidence, maintainability, simplification | `rdd_spark_critic` / `gpt-5.3-codex-spark` |
| Cross-file source grounding, runtime tradeoffs, reuse/refactor coupling, performance or accuracy uncertainty | `rdd_standard_critic` / `gpt-5.4-mini` |
| Security, data correctness, architecture blockers, broad migrations | `rdd_deep_critic` / `gpt-5.5` |
| Main implementation | Current main model; do not pin to Spark. |

Generated briefs may include `custom_agent_name`, `model`, `sandbox`, `brief_path`, `escalate_to`, and `escalate_when`.

Spawn plans are prompt scaffolds only. They do not claim that a subagent ran.
