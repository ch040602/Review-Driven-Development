# First-run questionnaire / 첫 실행 질문

Ask these once per target project when `.codex/review-driven-development/defaults.json` is missing. Save the exact answer to `profile.md`.

## Required questions

1. 기본 응답 언어는 한국어(`ko`)와 영어(`en`) 중 무엇인가요? / Which user-facing language should be the default?
2. 문서화 언어는 한국어와 영어 중 무엇인가요? / Which documentation language should be the default?
3. 기존 코드가 있다면 기본 처리 방침은 무엇인가요? `reuse_as_is`, `review_then_reuse`, `refactor_then_reuse`, `replace`, `isolate`, `ask_each_time`.
4. 기본 구현 방식은 무엇인가요? `tdd_first_incremental`, `prototype_then_harden`, `refactor_then_extend`, `research_experiment_first`.
5. 완성도와 실행 속도 중 무엇을 우선하나요? 기본값은 완성도입니다.
6. 기본 test/lint/build/eval 명령이 있나요?
7. TODO 완료 후 문서화 범위는 무엇인가요? `implementation_log_only`, `README/docs`, `ADR`, `CHANGELOG`.
8. CSV/log/data 파일이 있으면 별도 data critic을 항상 실행할까요?
9. 외부 skill은 `external-skill-links.md`의 링크를 확인한 뒤 사용해도 되나요?
10. destructive change, dependency 추가, public API 변경은 매번 확인할까요?

## Persistence rule

- Save exact response to `profile.md`.
- Save parsed defaults to `defaults.json`.
- On later runs, do not repeat these questions unless the new task conflicts with saved defaults.
