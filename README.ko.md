# review-driven-development

[![CI](https://github.com/YOUR_GITHUB_USERNAME/review-driven-development/actions/workflows/ci.yml/badge.svg)](https://github.com/YOUR_GITHUB_USERNAME/review-driven-development/actions/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-blue)](#필요-환경)
[![Codex Skill](https://img.shields.io/badge/Codex-Skill-black)](https://developers.openai.com/codex/skills)

> 요구사항 분석 → source/file 분석 → 비판 전용 subagent → TODO → TDD 검증 → 독립 review → 문서화 → 개선 loop를 강제하는 Codex custom skill입니다.

English README: [README.en.md](README.en.md)

## 목적

복잡한 개발·연구 작업에서는 빠른 구현보다 중요한 단계가 있습니다. 요구사항을 명확히 하고, 기존 코드를 재사용할지 판단하고, 테스트로 증명하고, 독립 review를 받고, 문서까지 남겨야 합니다. `review-driven-development`는 이 과정을 하나의 Codex skill workflow로 묶습니다.

핵심 원칙은 다음입니다.

- 첫 실행 질문을 통해 프로젝트 기본값을 저장합니다.
- 텍스트뿐 아니라 Markdown, README, AGENTS.md, source file, test, data file까지 분석합니다.
- 토론·검증·개선 단계의 subagent는 비판만 수행합니다.
- 한 번에 하나의 TODO만 진행합니다.
- 검증 evidence, 독립 review evidence, 문서화 상태 없이는 TODO를 완료하지 않습니다.

## 주요 기능

| 영역 | 포함 내용 |
|---|---|
| Skill 진입점 | `skills/review-driven-development/SKILL.md` |
| 영구 상태 | `.codex/review-driven-development/profile.md`, `defaults.json`, ledger |
| 요구사항 분석 | 언어, 구현 방식, 기존 코드 처리, 장단점 옵션화 |
| source/file 분석 | Markdown, README, AGENTS.md, source, tests, build files, CSV/data files |
| 비판 subagent | pre-plan, validation, improvement brief 생성 |
| TODO lifecycle | append-only TODO ledger, 한 개 active TODO 규칙 |
| 검증 | test/lint/build/eval quality-gate report |
| 문서화 gate | README/docs/ADR/changelog/implementation-log 점검 |
| 외부 skill 정책 | 공식/community skill URL과 trust policy |
| 테스트 | `self_test.py`, `pytest` smoke workflow test |

## 필요 환경

- Python 3.10+
- 테스트 실행용 `pytest`
- custom skill을 지원하는 Codex 환경
- 선택: PR/comment workflow용 GitHub CLI `gh`

```bash
python -m pip install -U pip pytest
```

## Codex skill 설치

### repo-local 설치

특정 repository에서만 사용하려면 다음을 사용합니다.

```bash
mkdir -p .agents/skills
cp -R skills/review-driven-development .agents/skills/review-driven-development
python .agents/skills/review-driven-development/scripts/validate_skill.py \
  --skill-dir .agents/skills/review-driven-development
```

### user-local 설치

여러 repository에서 개인 skill로 사용하려면 다음을 사용합니다.

```bash
mkdir -p ~/.agents/skills
cp -R skills/review-driven-development ~/.agents/skills/review-driven-development
python ~/.agents/skills/review-driven-development/scripts/validate_skill.py \
  --skill-dir ~/.agents/skills/review-driven-development
```

Codex에서 확인:

```text
/skills
```

명시 호출:

```text
$review-driven-development
```

## 빠른 시작

검증:

```bash
python -m compileall -q -f skills/review-driven-development/scripts
python skills/review-driven-development/scripts/validate_skill.py \
  --skill-dir skills/review-driven-development
python skills/review-driven-development/scripts/self_test.py
pytest -q
```

프로젝트 상태 생성:

```bash
python skills/review-driven-development/scripts/rdd_state.py --root . ensure
python skills/review-driven-development/scripts/rdd_state.py --root . init-defaults \
  --answers "한국어 응답, 한국어 문서화, TDD 우선, 기존 코드는 리뷰 후 재사용"
```

프로젝트 inventory 생성:

```bash
python skills/review-driven-development/scripts/context_inventory.py --root . --save --summary
```

TODO 생성 및 시작:

```bash
python skills/review-driven-development/scripts/todo_manager.py --root . create \
  "workflow smoke test 추가" \
  --acceptance "pytest passes" \
  --risk medium

python skills/review-driven-development/scripts/todo_manager.py --root . start-next
```

검증 evidence 기록:

```bash
python skills/review-driven-development/scripts/quality_gate.py \
  --root . \
  --todo-id RDD-T-00000001 \
  --kinds test,lint,build \
  --record-todo-evidence
```

실제 명령을 실행하려면 `.codex/review-driven-development/commands.json`을 작성합니다.

```json
{
  "test": ["pytest -q"],
  "lint": [],
  "build": [],
  "eval": []
}
```

그 뒤 실행:

```bash
python skills/review-driven-development/scripts/quality_gate.py \
  --root . \
  --todo-id RDD-T-00000001 \
  --kinds test,lint,build \
  --execute \
  --record-todo-evidence
```

독립 review와 문서화 상태 기록:

```bash
python skills/review-driven-development/scripts/todo_manager.py --root . review \
  RDD-T-00000001 \
  --summary "독립 검증 완료. blocker/high finding 없음."

python skills/review-driven-development/scripts/todo_manager.py --root . docs \
  RDD-T-00000001 \
  updated \
  --target README.md \
  --target .codex/review-driven-development/implementation-log.md
```

TODO 완료:

```bash
python skills/review-driven-development/scripts/todo_manager.py --root . complete RDD-T-00000001
```

## 작동 방식

```text
요구사항/파일/문서/데이터
→ 첫 실행 profile/defaults 저장
→ context inventory 생성
→ critical-only subagent brief 생성
→ main agent가 accept/reject/defer 결정
→ accepted finding을 TODO로 변환
→ TODO 1개만 in_progress
→ TDD/quality gate 검증
→ 독립 review evidence
→ 문서화 status
→ completion gate
→ improvement critique
→ follow-up TODO
```

## 완료 조건

TODO는 아래 조건을 만족해야 완료됩니다.

1. acceptance criteria 존재
2. validation evidence 존재
3. 실제 quality-gate 명령이 설정된 경우, 실행된 passing evidence 존재
4. independent review evidence 존재
5. documentation status가 `updated` 또는 `not_needed`
6. unresolved blocker/high review finding 없음

## GitHub 설정

이 패키지는 다음 GitHub 설정 파일을 포함합니다.

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
```

업로드 전 placeholder를 교체하세요.

```bash
grep -R "YOUR_GITHUB_USERNAME" -n .
grep -R "@YOUR_GITHUB_USERNAME" -n .
```

자세한 내용은 [docs/github-setup.md](docs/github-setup.md)와 [GITHUB_UPLOAD_CHECKLIST.md](GITHUB_UPLOAD_CHECKLIST.md)를 참고하세요.

## 개발 검증

```bash
python -m pip install -U pip pytest
python -m compileall -q -f skills/review-driven-development/scripts
python skills/review-driven-development/scripts/validate_skill.py --skill-dir skills/review-driven-development
python skills/review-driven-development/scripts/self_test.py
pytest -q
```

## 라이선스

아직 오픈소스 라이선스를 선택하지 않았습니다. 공개 배포 전 `LICENSE` 파일을 추가하세요.
