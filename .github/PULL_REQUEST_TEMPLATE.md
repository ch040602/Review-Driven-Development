## Summary

<!-- What changed and why? -->

## Type of change

- [ ] README/docs
- [ ] Skill workflow
- [ ] Helper script
- [ ] Test/validation
- [ ] GitHub/repository configuration
- [ ] External skill registry

## Validation

- [ ] `python -m compileall -q -f skills/review-driven-development/scripts`
- [ ] `python skills/review-driven-development/scripts/validate_skill.py --skill-dir skills/review-driven-development`
- [ ] `python skills/review-driven-development/scripts/self_test.py`
- [ ] `pytest -q`

## Review-driven-development checklist

- [ ] Maintains the critical-only subagent contract
- [ ] Does not allow more than one active TODO
- [ ] Does not weaken TODO completion gates
- [ ] Updates README/docs when behavior changes
- [ ] Updates `VALIDATION.md` or test evidence when validation changes
- [ ] External skill links remain consistent if changed

## Risks / follow-up TODOs

<!-- List unresolved risks or intentionally deferred work. -->
