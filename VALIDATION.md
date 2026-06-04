# Validation evidence

Validation performed after README and GitHub repository polish.

## Static validation

```bash
python -m compileall -q -f skills/review-driven-development/scripts
python skills/review-driven-development/scripts/validate_skill.py --skill-dir skills/review-driven-development
python skills/review-driven-development/scripts/skill_registration.py --repo-root . --validate-only
python skills/review-driven-development/scripts/skill_registration_helper.py --skill-dir skills/review-driven-development --validate
```

Observed result:

```text
compile_ok
Skill validation report: ok True
skill_registration.py: VALID
skill_registration_helper.py: valid true
```

## Behavioral smoke validation

```bash
python skills/review-driven-development/scripts/self_test.py
pytest -q
```

Observed result:

```text
self_test.py: ok true
pytest: 11 passed
```

## What this proves

- `SKILL.md` layout and metadata are valid.
- Python helper scripts compile.
- Registration helper validates the skill folder.
- First-run default detection works.
- Accepted critic findings can become TODOs.
- One active TODO can be started.
- Validation/improvement phases are not generated before implementation.
- Quality-gate evidence can be saved and linked to the TODO ledger.
- If real commands are configured in `commands.json` or parsed defaults, dry-run quality-gate evidence alone cannot complete a TODO.
- Independent review evidence can be recorded through CLI.
- Documentation status can be recorded through CLI.
- TODO completion gate completes only after evidence/review/docs requirements are satisfied.
- Unresolved blocker/high review findings block completion.
- Resolved, rejected, or deferred blocker/high review findings do not block completion.
- External skill URLs are checked offline across `external-skills.json`, `references/external-skills.md`, and `references/external-skill-links.md`.

## GitHub packaging validation

The updated package includes:

```text
.github/workflows/ci.yml
.github/dependabot.yml
.github/PULL_REQUEST_TEMPLATE.md
.github/ISSUE_TEMPLATE/*.yml
.github/CODEOWNERS
CONTRIBUTING.md
SECURITY.md
SUPPORT.md
CODE_OF_CONDUCT.md
GITHUB_UPLOAD_CHECKLIST.md
docs/github-setup.md
pyproject.toml
```

## What this does not prove

- It does not prove that a real Codex subagent was spawned; scripts generate briefs and ledgers.
- It does not prove external/community skill installation; links and policy are present, but installation remains explicit.
- It does not prove project-specific tests pass until `commands.json` contains real test/lint/build/eval commands.
- It does not prove GitHub branch protection is enabled; that must be configured in the GitHub repository settings.

## Repo-local installation validation procedure

```bash
mkdir -p .agents/skills
cp -R skills/review-driven-development .agents/skills/review-driven-development
python skills/review-driven-development/scripts/skill_registration.py --scope repo --overwrite
```

Then open Codex in that repository and run `/skills` to confirm `review-driven-development` appears.
