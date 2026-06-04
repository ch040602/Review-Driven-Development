# Codex completion and skill registration guide

## 목적

이 문서는 `review-driven-development` skill 초안을 Codex로 완성하고, 대상 repository에 skill로 등록하는 절차를 정의합니다.

## 1. 외부 skill 링크 확인

먼저 다음 파일을 열어 외부 skill 링크와 trust tier를 확인합니다.

```text
skills/review-driven-development/references/external-skill-links.md
```

우선순위:

1. Official OpenAI docs/skills
2. 이미 로컬에 설치된 user inventory skill
3. 검토 완료된 community skill
4. Fallback reference workflow

Community skill을 사용할 때는 반드시 다음을 확인합니다.

```text
SKILL.md
scripts/
hooks/
required binaries
network/file mutation behavior
```

## 2. Codex로 helper 구현 검토/확장

대상 repository 또는 이 draft repository에서 Codex에게 다음처럼 지시합니다.

### Korean prompt

```text
$review-driven-development를 사용해 이 skill 자체를 완성해.

범위:
- scripts/*.py의 helper contract를 기준으로 필요한 확장 지점을 구현
- 함수명과 state schema는 유지
- 외부 skill 링크는 references/external-skill-links.md 기준으로 유지
- subagent는 토론/검증/개선 단계에서 critical-only로 유지
- TODO는 정확히 하나만 in_progress 가능
- 한 TODO 완료 시 test-driven-development 검증, independent validation, documentation, improvement critique를 모두 기록
- README.md의 영/한 구조 유지

완료 조건:
- python -m compileall scripts 통과
- scripts/validate_skill.py 통과
- references/script-contracts.md와 구현 불일치 없음
```

### English prompt

```text
Use $review-driven-development to complete this skill draft.

Scope:
- Implement required helper extension points in scripts/*.py according to the documented contracts
- Preserve function names and state schemas
- Preserve external skill links from references/external-skill-links.md
- Keep subagents critical-only during debate, validation, review, and improvement phases
- Enforce exactly one in_progress TODO
- After each TODO, record TDD validation, independent validation, documentation, and improvement critique
- Preserve the bilingual README.md structure

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

When a user-wide installation is preferred, copy the skill into the Codex user skill location configured for the environment. If the environment follows Codex defaults, repository-scoped `.agents/skills/` is safer for project-specific workflows because it travels with the repo.

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

After Codex modifies this skill, run:

```bash
python -m compileall -q -f skills/review-driven-development/scripts
python skills/review-driven-development/scripts/validate_skill.py --skill-dir skills/review-driven-development
python skills/review-driven-development/scripts/self_test.py
pytest -q
```

Do not treat compile-only success as workflow success.
