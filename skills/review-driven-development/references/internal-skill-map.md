# Internal skill map / 내부 skill 사용 지도

`review-driven-development` remains the single user-facing workflow. The skills below are invoked internally when present. External links are listed so Codex can locate or review the intended skill before using it.

## Current installed/local skills from the user inventory

| Skill | Use inside `review-driven-development` | Link policy |
|---|---|---|
| `.system` | Baseline system/tool behavior | local/system |
| `agentic-rag` | Companion workflow for Agentic RAG, cross-corpus retrieval, context sufficiency, query rewriting, and grounded synthesis tasks | local-current |
| `paper-summary-agent` | Research paper and scholarly source digestion | local-current |
| `research-idea-consensus` | Research idea critique and consensus synthesis | local-current |
| `prompt-graph-manager` | Prompt/workflow graph organization for AI/LLM tasks | local-current |
| `hatch-pet` | Not core; use only if project-specific | local-current |
| `awesome-design-md` | Markdown/design-oriented document handling if relevant | local-current |
| `csv-data-summarizer` | CSV/data profile, data quality, analysis summaries | local-current |
| `docx` | DOCX reading/writing workflows when documents are provided or required | local-current |
| `frontend-slides` | Slide generation for frontend/product communication if requested | local-current |
| `ios-simulator-skill` | iOS validation where app/platform requires simulator checks | local-current |
| `pdf` | PDF reading/writing workflows when PDFs are provided or required | local-current |
| `subagent-driven-development` | Parallel exploration, critique orchestration, multi-agent planning | local-current |
| `systematic-debugging` | Failure reproduction, localization, correction, regression guard | local-current |
| `test-driven-development` | Failing-test-first planning, acceptance tests, validation evidence | local-current |
| `webapp-testing` | Browser/webapp behavior validation | local-current |

## Official OpenAI skills/docs to use by link

| Skill/doc | Phase | Link |
|---|---|---|
| Codex skills docs | registration/design | https://developers.openai.com/codex/skills |
| Codex subagents docs | parallel critique | https://developers.openai.com/codex/subagents |
| Codex AGENTS.md docs | project instructions | https://developers.openai.com/codex/guides/agents-md |
| Codex GitHub review docs | PR review | https://developers.openai.com/codex/integrations/github |
| `skill-creator` | skill creation/refinement | https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md |
| `define-goal` | requirement clarification | https://github.com/openai/skills/blob/main/skills/.curated/define-goal/SKILL.md |
| `create-plan` | planning | https://github.com/openai/skills/blob/main/skills/.experimental/create-plan/SKILL.md |
| `gh-address-comments` | review comments -> TODOs | https://github.com/openai/skills/blob/main/skills/.curated/gh-address-comments/SKILL.md |
| `openai-docs` | OpenAI/Codex/API grounding | https://github.com/openai/skills/blob/main/skills/.curated/openai-docs/SKILL.md |

## Community skills to use by link after review

| Skill | Phase | Link |
|---|---|---|
| `using-agent-skills` | skill selection | https://github.com/addyosmani/agent-skills/blob/main/skills/using-agent-skills/SKILL.md |
| `spec-driven-development` | specification | https://github.com/addyosmani/agent-skills/blob/main/skills/spec-driven-development/SKILL.md |
| `planning-and-task-breakdown` | TODO generation | https://github.com/addyosmani/agent-skills/blob/main/skills/planning-and-task-breakdown/SKILL.md |
| `incremental-implementation` | sequential implementation | https://github.com/addyosmani/agent-skills/blob/main/skills/incremental-implementation/SKILL.md |
| `source-driven-development` | source/doc grounding | https://github.com/addyosmani/agent-skills/blob/main/skills/source-driven-development/SKILL.md |
| `test-driven-development` | validation | https://github.com/addyosmani/agent-skills/blob/main/skills/test-driven-development/SKILL.md |
| `debugging-and-error-recovery` | failure triage | https://github.com/addyosmani/agent-skills/blob/main/skills/debugging-and-error-recovery/SKILL.md |
| `code-review-and-quality` | review gate | https://github.com/addyosmani/agent-skills/blob/main/skills/code-review-and-quality/SKILL.md |
| `code-simplification` | refactor | https://github.com/addyosmani/agent-skills/blob/main/skills/code-simplification/SKILL.md |
| `documentation-and-adrs` | documentation | https://github.com/addyosmani/agent-skills/blob/main/skills/documentation-and-adrs/SKILL.md |
| `security-and-hardening` | security critique | https://github.com/addyosmani/agent-skills/blob/main/skills/security-and-hardening/SKILL.md |
| `performance-optimization` | efficiency critique | https://github.com/addyosmani/agent-skills/blob/main/skills/performance-optimization/SKILL.md |
| `api-and-interface-design` | interface critique | https://github.com/addyosmani/agent-skills/blob/main/skills/api-and-interface-design/SKILL.md |

## Invocation map by phase

| Phase | Primary skills |
|---|---|
| Requirement intake | `define-goal`, `source-driven-development`, `awesome-design-md`, `pdf`, `docx`, `paper-summary-agent` |
| Existing code understanding | `source-driven-development`, `subagent-driven-development`, `systematic-debugging` |
| Data understanding | `csv-data-summarizer` |
| Debate/critique | `subagent-driven-development`, `research-idea-consensus` |
| TODO generation | `create-plan`, `planning-and-task-breakdown`, `prompt-graph-manager` |
| Implementation | `incremental-implementation`, main agent, project tools |
| Testing | `test-driven-development`, `webapp-testing`, `ios-simulator-skill` |
| Failure triage | `systematic-debugging`, `debugging-and-error-recovery` |
| Review comments | `gh-address-comments`, Codex GitHub review |
| Documentation | `documentation-and-adrs`, `docx`, `pdf`, `frontend-slides` |
| AI/LLM eval | `openai-docs`, `prompt-graph-manager`, `research-idea-consensus`, `paper-summary-agent` |
| Agentic RAG / retrieval systems | `agentic-rag`, `source-driven-development`, `test-driven-development`, `code-review-and-quality` |

## Fallbacks

| Missing skill | Fallback |
|---|---|
| `source-driven-development` | Inspect files directly; cite filenames, symbols, and observed evidence in state logs |
| `markdown-context-reader` | Read Markdown files as requirements/specs and extract constraints/TODOs manually |
| `gh-address-comments` | Ask user to paste review comments or use local review notes |
| `documentation-and-adrs` | Use `references/documentation-policy.md` |
| `code-review-and-quality` | Use `references/subagent-roles.md` validation critics |
