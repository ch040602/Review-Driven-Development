# TODO policy / TODO 정책

## Statuses

```text
pending
in_progress
blocked
completed
deferred
```

## Hard rules

1. Exactly one TODO may be `in_progress`.
2. Every TODO must have acceptance criteria before implementation.
3. Every behavior-changing TODO should use `test-driven-development` when practical.
4. A TODO cannot be `completed` unless it has:
   - validation evidence
   - independent validation/review reference
   - documentation reference or explicit `not_needed` rationale
   - no unresolved blocker/high accepted finding
5. Improvement findings after a TODO become new TODOs only if accepted by the main agent.

## Recommended TODO shape

```text
small enough for one focused implementation slice
large enough to produce user-visible or test-visible value
explicit dependencies
explicit validation command or evidence
explicit documentation requirement
```
