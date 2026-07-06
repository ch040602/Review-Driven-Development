# Documentation policy

Completed TODOs must update documentation before being marked complete.

## Documentation targets

| Change type | Target |
|---|---|
| User-facing behavior | `README.md`, usage docs, examples |
| Public API/interface | API docs, OpenAPI/spec docs, examples |
| Architecture/design decision | `docs/adr/` |
| Release/user-visible change | `CHANGELOG.md` or release notes |
| Internal implementation detail | `.codex/review-driven-development/implementation-log.md` |
| Research/data analysis | methodology notes, data assumptions, eval results |

## Not-needed rule

If no public documentation is needed, record a short rationale in `implementation-log.md` and attach that entry as a TODO documentation reference.

## Bilingual rule

Use saved `defaults.json` language settings. Preserve code names, commands, paths, and API terms in their original language.
