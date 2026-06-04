# Contributing

Thank you for improving `review-driven-development`.

## Development setup

```bash
python -m pip install -U pip pytest
python -m compileall -q -f skills/review-driven-development/scripts
python skills/review-driven-development/scripts/validate_skill.py --skill-dir skills/review-driven-development
python skills/review-driven-development/scripts/self_test.py
pytest -q
```

## Pull request rules

Before opening a PR:

1. Keep the change focused.
2. Preserve the critical-only subagent contract.
3. Preserve the one-active-TODO rule.
4. Do not weaken TODO completion gates.
5. Update tests when workflow behavior changes.
6. Update README/docs when user-facing behavior changes.
7. Update external skill registries if any skill link changes.

## Areas that need extra care

- `skills/review-driven-development/SKILL.md`
- `skills/review-driven-development/references/workflow.md`
- `skills/review-driven-development/references/subagent-roles.md`
- `skills/review-driven-development/scripts/todo_manager.py`
- `skills/review-driven-development/scripts/workflow_runner.py`
- `skills/review-driven-development/scripts/quality_gate.py`
- `external-skills.json`

## Validation evidence

Include command output in the PR description when changing workflow or helper scripts.
