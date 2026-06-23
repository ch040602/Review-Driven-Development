# Minimal solution policy

RDD runs a minimal-change gate before TODO generation when the task can create new work.

## Ladder

1. Is this feature necessary for a current acceptance criterion?
2. Can existing code, state, or docs handle it?
3. Can stdlib, native platform behavior, or an installed dependency handle it?
4. Can the change be one direct line or one local call?
5. If still necessary, implement the smallest local code path.

## Minimalism levels

| Level | Meaning |
|---|---|
| `off` | Do not run minimality gates. |
| `lite` | Run the ladder only for dependency/config/new-file changes. |
| `full` | Default. Run the ladder before TODO generation and use diff budget after edits. |
| `ultra` | Require simplification-critic review for every logic change. |

## Required evidence

- `minimality_packet.json` records the selected rung, reuse candidates, skipped ideas, and the condition that would justify adding more.
- `diff_budget.py` records touched files, added LOC, new classes, dependency/config additions, and missing-test blockers.
- `dependency_guard.py` blocks dependency additions unless the minimality packet and `decision-log.md` justify them.
- `rdd-debt.jsonl` records simplification candidates that are useful but outside the current TODO.

The packet is evidence for the main agent, not an automatic decision.
