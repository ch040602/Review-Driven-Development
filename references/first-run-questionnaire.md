# First-run questionnaire

Ask these once per target project when `.codex/review-driven-development/defaults.json` is missing. Save the exact answer to `profile.md`.

## Required questions

1. Which user-facing language should be the default? `ko` or `en`.
2. Which language should documentation use by default? `ko` or `en`.
3. If existing code exists, what is the default code policy? `reuse_as_is`, `review_then_reuse`, `refactor_then_reuse`, `replace`, `isolate`, `ask_each_time`.
4. What implementation strategy should be used by default? `tdd_first_incremental`, `prototype_then_harden`, `refactor_then_extend`, `research_experiment_first`.
5. What takes priority: completeness or speed? Default is completeness.
6. Are there default test/lint/build/eval commands?
7. What is the documentation scope after TODO completion? `implementation_log_only`, `README/docs`, `ADR`, `CHANGELOG`.
8. If CSV/log/data files are present, should the data critic always run?
9. Should external skills be used only after checking links in `external-skill-links.md`?
10. Should destructive changes, dependency additions, and public API updates be acknowledged every time?

## Persistence rule

- Save exact response to `profile.md`.
- Save parsed defaults to `defaults.json`.
- On later runs, do not repeat these questions unless the new task conflicts with saved defaults.
