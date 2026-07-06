# Codex completion and skill registration guide

This document defines how to complete the `review-driven-development` skill draft with Codex and register it in a target repository.

## 1. Verify external skill links

Open this file first:

```text
skills/review-driven-development/references/external-skill-links.md
```

Priority:

1. Official OpenAI docs/skills
2. User-installed local `inventory` skill
3. Reviewed community skill
4. Fallback reference workflow

Before using a community skill, confirm:

```text
SKILL.md
scripts/
hooks/
required binaries
network and file-mutation behavior
```

## 2. Review or extend helper implementation in Codex

In the target repository (or this draft repository), instruct Codex as follows:

### English prompt

```text
Use $review-driven-development to complete this skill draft.

Scope:
- Implement required helper extension points in scripts/*.py based on documented contracts
- Preserve function names and state schemas
- Keep external skill links aligned with references/external-skill-links.md
- Keep subagents critical-only during debate, validation, and improvement phases
- Allow exactly one `in_progress` TODO at a time
- For each completed TODO, record TDD validation, independent validation, documentation updates, and improvement critique
- Preserve README and workflow policies

Completion criteria:
- python -m compileall scripts passes
- scripts/validate_skill.py passes
- implementation matches references/script-contracts.md
```

### English prompt

```text
Use $review-driven-development to complete this skill draft.

Scope:
- Implement required helper extension points in scripts/*.py according to documented contracts
- Preserve function names and state schemas
- Preserve external skill links from references/external-skill-links.md
- Keep subagents critical-only during debate, validation, review, and improvement phases
- Enforce exactly one in_progress TODO
- After each TODO, record TDD validation, independent validation, documentation, and improvement critique
- Keep README workflow contracts consistent

Completion criteria:
- python -m compileall scripts passes
- scripts/validate_skill.py passes
- implementation matches references/script-contracts.md
```

## 3. Local validation

From this draft root:

```bash
python skills/review-driven-development/scripts/validate_skill.py --skill-dir skills/review-driven-development
python -m compileall skills/review-driven-development/scripts
```

## 4. Repo-scoped registration

From the target repository root:

```bash
mkdir -p .agents/skills
cp -R /path/to/review-driven-development/skills/review-driven-development .agents/skills/
```

Then validate:

```bash
python .agents/skills/review-driven-development/scripts/validate_skill.py --skill-dir .agents/skills/review-driven-development
```

Invoke:

```text
Use $review-driven-development for this requirement.
```

## 5. User-scoped registration

When user-wide installation is preferred, copy the skill into the Codex user skill location configured for the environment. If the environment follows Codex defaults, repository-scoped `.agents/skills/` is safer for project-specific workflows because it travels with the repository.

## 6. First run checklist

On first use in a target project, the agent should:

1. Read `AGENTS.md`, README, docs, source files, tests, build files, and data files.
2. Build a context inventory with `context_inventory.py`.
3. Ask the first-run questionnaire.
4. Save exact answers to `profile.md`.
5. Save parsed defaults to `defaults.json`.
6. Generate critical-only preplan subagent briefs.
7. Convert accepted findings into TODOs.
8. Execute one TODO only.
9. Validate with TDD and independent critical review.
10. Document the completed work.
11. Run improvement critique and update TODOs.

## 7. Registration evidence to record

After registration or completion, append this to `implementation-log.md`:

```text
- skill path
- validation command
- validation result
- external skill links reviewed
- local skills detected
- known limitations
- next TODO
```

## Required behavioral validation

```bash
python -m compileall -q -f skills/review-driven-development/scripts
python skills/review-driven-development/scripts/validate_skill.py --skill-dir skills/review-driven-development
python skills/review-driven-development/scripts/self_test.py
pytest -q
```

Codex should not report the workflow as validated if only static checks were run.
