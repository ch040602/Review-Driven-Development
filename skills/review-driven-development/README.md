# review-driven-development Codex Skill

## 한국어

이 폴더는 `review-driven-development` Codex custom skill입니다. 목적은 요구사항 분석, source/docs/data 이해, 비판 전용 subagent 토론, TODO 생성, TODO별 TDD 검증, 독립 review, 문서화, 개선 TODO 갱신을 하나의 workflow로 통합하는 것입니다.

### 주요 파일

| 경로 | 역할 |
|---|---|
| `SKILL.md` | Codex skill 진입점 |
| `references/workflow.md` | 전체 workflow |
| `references/subagent-roles.md` | critical-only subagent 역할 |
| `references/internal-skill-map.md` | 내부/외부 skill 사용 지도 |
| `references/external-skill-links.md` | 외부 skill URL source of truth |
| `references/script-contracts.md` | Python script 구현 계약 |
| `references/function-scaffold.md` | 실제 `scripts/*.py` 함수 계약 |
| `references/codex-completion-and-registration.md` | Codex로 완성하고 등록하는 절차 |
| `scripts/*.py` | 상태/TODO/비판/검증/문서화 helper |

### 빠른 context/cache 사용

```bash
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --summary
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --overview
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-summary
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-search "quality gate completion"
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --bootstrap
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase commands
```

`context-pack.md`는 Codex가 먼저 읽는 compact summary이고, `context-cache.json`은 safe cache reuse용 fingerprint metadata입니다. `context-semantic-index.json`은 파일/심볼/용어 locator이며, 기본 `--semantic-search`는 TF-IDF, lexical fallback 순서로 ranking합니다. dense embedding ranking은 `--embeddings`로 opt-in합니다. `--sync --bootstrap`은 repo-local `AGENTS.md`에 fast-context block을 자동 주입합니다.

기본 smoke test는 embedding model load를 피합니다. 실제 embedding 검증은 `python skills/review-driven-development/scripts/self_test.py --embeddings`로 실행합니다.

### 검증

```bash
python scripts/validate_skill.py --skill-dir .
python -m compileall scripts
```

### 등록

Repository root 기준:

```bash
mkdir -p .agents/skills
cp -R /path/to/review-driven-development .agents/skills/review-driven-development
```

외부 skill은 `references/external-skill-links.md`의 링크를 기준으로 확인합니다. Community skill은 사용 전 `SKILL.md`, scripts, hooks, 권한 요구사항을 검토해야 합니다.

### 있으면 좋은 외부/companion skill

| Skill | 용도 | Link |
|---|---|---|
| `agentic-rag` | Agentic RAG, cross-corpus retrieval, context sufficiency, query rewriting, grounded synthesis 관련 TODO를 RDD 내부 companion workflow로 보조 | https://github.com/ch040602/Agentic-RAG-Skill |

---

## English

This folder contains the `review-driven-development` Codex custom skill. It integrates requirement analysis, source/docs/data understanding, critical-only subagent debate, TODO generation, TDD validation per TODO, independent review, documentation, and improvement TODO updates into one workflow.

### Main files

| Path | Purpose |
|---|---|
| `SKILL.md` | Codex skill entrypoint |
| `references/workflow.md` | End-to-end workflow |
| `references/subagent-roles.md` | Critical-only subagent roles |
| `references/internal-skill-map.md` | Internal/external skill map |
| `references/external-skill-links.md` | Source of truth for external skill URLs |
| `references/script-contracts.md` | Python script implementation contract |
| `references/function-scaffold.md` | Actual `scripts/*.py` function contract |
| `references/codex-completion-and-registration.md` | How to complete and register with Codex |
| `scripts/*.py` | Helpers for state/TODO/critique/validation/docs |

### Fast context/cache use

```bash
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --summary
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --overview
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-summary
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --semantic-search "quality gate completion"
python skills/review-driven-development/scripts/context_inventory.py --root . --sync --bootstrap
python skills/review-driven-development/scripts/workflow_runner.py --root . --phase commands
```

`context-pack.md` is the compact summary Codex should read first. `context-cache.json` stores fingerprint metadata for safe cache reuse. `context-semantic-index.json` is the file/symbol/term locator, default `--semantic-search` ranks with TF-IDF then lexical fallback, dense embedding ranking is opt-in with `--embeddings`, and `--sync --bootstrap` injects a fast-context block into repo-local `AGENTS.md`.

Default smoke validation avoids embedding model loading. Run `python skills/review-driven-development/scripts/self_test.py --embeddings` for explicit embedding validation.

### Validate

```bash
python scripts/validate_skill.py --skill-dir .
python -m compileall scripts
```

### Register

From a repository root:

```bash
mkdir -p .agents/skills
cp -R /path/to/review-driven-development .agents/skills/review-driven-development
```

External skills must be checked through `references/external-skill-links.md`. Community skills should be reviewed for `SKILL.md`, scripts, hooks, and permissions before use.

### Useful External/Companion Skills

| Skill | Use | Link |
|---|---|---|
| `agentic-rag` | Optional companion workflow for Agentic RAG, cross-corpus retrieval, context sufficiency, query rewriting, and grounded synthesis TODOs inside RDD | https://github.com/ch040602/Agentic-RAG-Skill |


## 검증/Validation

이 패키지는 정적 검증뿐 아니라 `self_test.py`와 `pytest` 기반 behavioral smoke test를 포함합니다. 자세한 결과는 `VALIDATION.md`와 `REVIEW_NOTES.md`를 확인하십시오.

```bash
python -m compileall -q -f skills/review-driven-development/scripts
python skills/review-driven-development/scripts/validate_skill.py --skill-dir skills/review-driven-development
python skills/review-driven-development/scripts/self_test.py
pytest -q
```
