# Subagent roles

All critique, validation, and improvement subagents are critical-only.

## Contract

A subagent must:

- identify risks, missing evidence, contradictions, regressions, inefficiencies, and weak assumptions,
- avoid praise,
- avoid final decisions,
- avoid patches unless explicitly asked in a non-critic phase,
- return structured findings.

The main agent decides whether to accept, reject, defer, or ask the user.

## Pre-plan roles

| Role | Critical focus |
|---|---|
| `requirements-critic` | Ambiguity, missing acceptance criteria, contradictory requirements. |
| `language-runtime-critic` | Language/runtime tradeoffs, ecosystem risks, deployment constraints. |
| `architecture-critic` | Coupling, boundaries, scaling, rollback, data flow. |
| `existing-code-reuse-refactor-critic` | Whether existing code should be reused, reviewed, refactored, isolated, or replaced. |
| `source-grounding-critic` | Unsupported API/framework assumptions and missing official sources. |
| `markdown-doc-context-critic` | Whether AGENTS.md, README, docs, and Markdown specs were actually read. |
| `test-tdd-critic` | Test strategy, failing-test-first proof, coverage, regression protection. |
| `security-risk-critic` | Input, auth, secrets, dependency, data, and destructive-change risks. |
| `documentation-critic` | Missing docs/ADR/changelog/API examples. |
| `data-csv-critic` | Schema, nulls, duplicates, leakage, metric errors, CSV/log problems. |

## Validation roles

| Role | Critical focus |
|---|---|
| `validation-runner-critic` | Whether evidence actually proves the TODO. |
| `test-tdd-critic` | Whether tests protect behavior and include regressions. |
| `security-risk-critic` | Whether implementation introduced security risks. |
| `documentation-critic` | Whether documentation matches the change. |
| `maintainability-critic` | Whether code is reviewable and maintainable. |

## Improvement roles

| Role | Critical focus |
|---|---|
| `quality-critic` | Correctness, completeness, edge cases. |
| `performance-efficiency-critic` | Runtime, memory, query, bundle, and data-processing inefficiency. |
| `accuracy-evaluation-critic` | Accuracy, eval set quality, LLM/RAG regressions. |
| `data-csv-critic` | Dataset/CSV/log issues and metric reliability. |
| `documentation-critic` | Missing or inaccurate docs. |
| `maintainability-critic` | Complexity, duplication, naming, boundaries. |

## Finding format

```yaml
- finding_id: RDD-ROLE-001
  severity: blocker | high | medium | low
  area: requirements | architecture | language | reuse | tests | security | docs | data | performance | accuracy | maintainability | source
  claim: ""
  risk: ""
  missing_evidence: ""
  recommendation: ""
  check: ""
```
