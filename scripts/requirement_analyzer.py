#!/usr/bin/env python3
"""Requirement analysis helper.

This module prepares the first response for `review-driven-development`:
- summarize known requirements
- identify source/docs/data context
- propose language/runtime/method options with pros and cons
- ask first-run questions when defaults are missing
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Dict, Iterable, List, Mapping, Optional

try:
    from .context_inventory import build_inventory, load_inventory
    from .rdd_state import load_defaults
except ImportError:  # pragma: no cover
    from context_inventory import build_inventory, load_inventory  # type: ignore
    from rdd_state import load_defaults  # type: ignore


@dataclass
class Option:
    """A candidate option with tradeoffs."""

    name: str
    advantages: List[str]
    disadvantages: List[str]
    when_to_choose: str


@dataclass
class RequirementPacket:
    """Structured packet consumed by planning and critic phases."""

    prompt_summary: str
    constraints: List[str]
    open_questions: List[str]
    language_options: List[Option]
    method_options: List[Option]
    existing_code_options: List[Option]
    validation_options: List[Option]
    documentation_options: List[Option]
    context_summary: Dict[str, object]


def summarize_prompt(prompt: str) -> str:
    """Create a compact prompt summary.

    The summary is deterministic and extractive: it keeps leading intent,
    explicit file references, and hard-constraint lines instead of inventing a
    paraphrase.
    """

    lines = [line.strip() for line in prompt.strip().splitlines() if line.strip()]
    if not lines:
        return "No prompt text provided."

    normalized = " ".join(prompt.strip().split())
    file_refs = sorted(set(re.findall(r"[\w./\\-]+\.(?:py|md|json|toml|yaml|yml|txt|csv|tsv|jsonl|pdf|docx)", prompt, flags=re.IGNORECASE)))
    constraint_lines = extract_constraints(prompt)
    parts = [f"Intent: {normalized[:700]}"]
    if file_refs:
        parts.append("Referenced files: " + ", ".join(file_refs[:20]))
    if constraint_lines:
        parts.append("Hard constraints: " + " | ".join(constraint_lines[:8]))
    return "\n".join(parts)[:1600]


def extract_constraints(prompt: str, markdown_texts: Optional[Iterable[str]] = None) -> List[str]:
    """Extract hard constraints from prompt and Markdown text.

    Uses conservative keyword and imperative-pattern heuristics. It is intended
    to surface likely constraints for the main agent and critics, not to make a
    final decision.
    """

    constraints: List[str] = []
    combined = "\n".join([prompt, *(markdown_texts or [])])
    keywords = [
        "must", "required", "requirement", "do not", "don't", "never", "cannot",
        "필수", "반드시", "하지마", "하지 마", "금지", "지원", "완성도", "검증", "문서화", "완료 조건", "TDD",
    ]
    for line in combined.splitlines():
        stripped = line.strip(" \t-*>")
        lowered = stripped.lower()
        looks_numbered = bool(re.match(r"^\d+[.)]\s+", stripped))
        if stripped and (any(keyword.lower() in lowered for keyword in keywords) or looks_numbered):
            if stripped not in constraints:
                constraints.append(stripped)
    return constraints[:80]


def infer_language_options(context: Mapping[str, object]) -> List[Option]:
    """Infer plausible implementation languages from inventory.

    Combines language counts, build manifests, lockfiles, and framework hints so
    helper scripts can recommend runtimes without reading dependency trees in
    depth.
    """

    languages = context.get("language_counts", {}) if isinstance(context.get("language_counts"), dict) else {}
    build_files = {Path(str(item)).name.lower() for item in context.get("build_files", []) if isinstance(item, str)}
    frameworks = {str(item).lower() for item in context.get("frameworks", []) if isinstance(item, str)}
    options: List[Option] = []
    for language, count in sorted(languages.items(), key=lambda item: item[1], reverse=True)[:5]:
        advantages = [f"Existing project evidence: {count} files", "Lowest integration cost if current code is reused"]
        if str(language).startswith("typescript") and any(name in build_files for name in {"package.json", "tsconfig.json"}):
            advantages.append("TypeScript manifests are present")
        if str(language) == "python" and any(name in build_files for name in {"pyproject.toml", "requirements.txt"}):
            advantages.append("Python dependency manifests are present")
        options.append(Option(
            name=str(language),
            advantages=advantages,
            disadvantages=["May inherit current architecture limitations", "May not be ideal for new isolated tooling"],
            when_to_choose="Choose when existing code reuse/refactor is preferred.",
        ))
    inferred = [
        ("node/typescript", {"package.json", "pnpm-lock.yaml", "yarn.lock", "package-lock.json", "tsconfig.json"}, ["Matches detected Node/TypeScript manifests", "Good fit for web/app workflows"]),
        ("python", {"pyproject.toml", "requirements.txt", "Pipfile"}, ["Matches detected Python manifests", "Good fit for scripts, tests, research, and data tooling"]),
        ("rust", {"cargo.toml"}, ["Matches Cargo manifest", "Good fit for performance-sensitive CLI/library work"]),
        ("go", {"go.mod"}, ["Matches Go module manifest", "Good fit for services and small tools"]),
    ]
    existing_names = {option.name for option in options}
    for name, markers, advantages in inferred:
        if name not in existing_names and markers & build_files:
            options.append(Option(name, advantages, ["Requires integration with existing code boundaries"], "Choose when manifest evidence matches the TODO."))
    if frameworks and options:
        options[0].advantages.append("Framework hints: " + ", ".join(sorted(frameworks)[:8]))
    if not options:
        options.append(Option(
            name="python",
            advantages=["Fast research/tooling iteration", "Good data analysis and scripting ecosystem"],
            disadvantages=["May not match production runtime", "Requires integration planning for non-Python apps"],
            when_to_choose="Choose for research automation, data analysis, or helper scripts.",
        ))
    return options


def build_method_options() -> List[Option]:
    """Return implementation method options with pros and cons."""

    return [
        Option("tdd_first_incremental", ["Strong regression guard", "Clear evidence per TODO"], ["Slower setup", "Harder for UI/prototype-only tasks"], "Default for behavior changes."),
        Option("prototype_then_harden", ["Fast exploration", "Useful when requirements are uncertain"], ["Needs cleanup pass", "Higher regression risk before tests"], "Use for research spikes or unknown APIs."),
        Option("refactor_then_extend", ["Reduces complexity before adding features", "Improves long-term maintainability"], ["Can increase upfront scope", "Requires strong tests"], "Use when existing code blocks safe implementation."),
    ]


def build_existing_code_options(has_existing_code: bool) -> List[Option]:
    """Return reuse/review/refactor/rewrite options."""

    if not has_existing_code:
        return [Option("new_implementation", ["No legacy constraints"], ["Must create tests/docs from scratch"], "Use when no meaningful existing code exists.")]
    return [
        Option("reuse_as_is", ["Smallest change", "Lower immediate cost"], ["May preserve hidden defects"], "Use only when code is covered and fit for purpose."),
        Option("review_then_reuse", ["Balances speed and safety", "Finds obvious defects first"], ["Requires review time"], "Default for existing code."),
        Option("refactor_then_reuse", ["Improves maintainability", "Reduces future risk"], ["Requires tests and migration care"], "Use when code is useful but hard to extend."),
        Option("replace", ["Clean design possible"], ["Highest regression and migration risk"], "Use when existing code is unsafe or incompatible."),
    ]


def build_validation_options(has_tests: bool) -> List[Option]:
    """Return validation strategy options."""

    return [
        Option("existing_tests_plus_targeted_tests", ["Uses current safety net", "Efficient"], ["Existing tests may be weak"], "Use when tests already exist." if has_tests else "Use after creating baseline tests."),
        Option("new_acceptance_tests", ["Directly proves requirement", "Good for TDD"], ["Needs test harness work"], "Use for new behavior."),
        Option("manual_or_eval_evidence", ["Useful for UI/research outputs", "Can capture qualitative behavior"], ["Less repeatable than automated tests"], "Use when automation is not yet feasible."),
    ]


def build_documentation_options() -> List[Option]:
    """Return documentation strategy options."""

    return [
        Option("implementation_log_only", ["Low overhead", "Good traceability"], ["Not user-facing"], "Use for internal-only changes."),
        Option("readme_or_usage_docs", ["User-facing clarity", "Good for behavior changes"], ["Requires maintenance"], "Use for changed usage/API behavior."),
        Option("adr_plus_docs", ["Captures design rationale", "Useful for future review"], ["More writing overhead"], "Use for architecture or irreversible decisions."),
    ]


def _infer_response_language(context: Mapping[str, object]) -> str:
    """Infer Korean or English for first-run text from saved hints/snippets."""

    language = context.get("language")
    if isinstance(language, Mapping):
        user_facing = language.get("user_facing")
        if str(user_facing).lower() in {"ko", "en"}:
            return str(user_facing).lower()
    snippets = context.get("doc_snippets", {})
    text = json.dumps(snippets, ensure_ascii=False) if isinstance(snippets, Mapping) else ""
    return "ko" if re.search(r"[가-힣]", text) else "en"


def build_first_run_questions(context: Mapping[str, object]) -> List[str]:
    """Build first-run questions based on context.

    Questions are localized to Korean or English using saved language hints or
    detected Markdown snippets. The defaults remain conservative if omitted.
    """

    if _infer_response_language(context) == "en":
        questions = [
            "What should the default response language be: Korean or English?",
            "What should the documentation language be: Korean, English, or both?",
            "For existing code, should the default policy be reuse, review then reuse, refactor, partial replacement, full rewrite, or decide per TODO?",
            "Which implementation method should be the default: TDD first, prototype then harden, or refactor then extend?",
            "What default test/lint/build/eval commands should be recorded?",
            "After each TODO, should documentation be implementation-log only, README/docs, ADR, CHANGELOG, or a combination?",
        ]
        if context.get("requires_data_critic") or context.get("data_files"):
            questions.append("Should CSV/log/data files be reviewed by a data critic after each relevant TODO?")
        return questions

    questions = [
        "기본 응답 언어는 한국어/영어 중 무엇으로 할까요?",
        "문서화 언어는 한국어/영어/둘 다 중 무엇으로 할까요?",
        "기존 코드가 있다면 재사용, 리뷰 후 재사용, 리팩터링, 부분 교체, 전면 재작성, TODO별 판단 중 어떤 방침을 기본값으로 할까요?",
        "선호 구현 방식은 TDD 우선, prototype 후 hardening, refactor 후 확장 중 무엇인가요?",
        "기본 test/lint/build/eval 명령이 있으면 알려주세요.",
        "TODO 완료 후 문서화 범위는 implementation-log만, README/docs, ADR, CHANGELOG 포함 중 무엇인가요?",
    ]
    if context.get("requires_data_critic") or context.get("data_files"):
        questions.append("CSV/log/data 파일은 별도 data critic이 매 TODO 이후 검토하도록 할까요?")
    return questions


def create_requirement_packet(prompt: str, root: Path, *, saved_inventory: bool = True) -> RequirementPacket:
    """Create a structured requirement packet for critic/planning phases."""

    context = load_inventory(root) if saved_inventory else {}
    if not context:
        context = build_inventory(root)
    markdown_texts = context.get("doc_snippets", {}).values() if isinstance(context.get("doc_snippets"), Mapping) else []
    constraints = extract_constraints(prompt, markdown_texts)
    return RequirementPacket(
        prompt_summary=summarize_prompt(prompt),
        constraints=constraints,
        open_questions=build_first_run_questions(context) if load_defaults(root) is None else [],
        language_options=infer_language_options(context),
        method_options=build_method_options(),
        existing_code_options=build_existing_code_options(bool(context.get("has_existing_code"))),
        validation_options=build_validation_options(bool(context.get("has_tests"))),
        documentation_options=build_documentation_options(),
        context_summary=dict(context),
    )


def render_packet_markdown(packet: RequirementPacket, *, language: str = "ko") -> str:
    """Render a first-response packet with pros/cons.

    Renders Korean or English labels while preserving identifiers, commands, and
    file paths. Context citations come from the inventory file lists.
    """

    def render_options(title: str, options: List[Option]) -> str:
        lines = [f"## {title}"]
        for option in options:
            lines.extend([
                f"### {option.name}",
                f"- 장점/Advantages: {', '.join(option.advantages)}",
                f"- 단점/Disadvantages: {', '.join(option.disadvantages)}",
                f"- 선택 기준/When: {option.when_to_choose}",
            ])
        return "\n".join(lines)

    label_map = {
        "ko": {
            "title": "요구사항 패킷",
            "summary": "요약",
            "constraints": "제약",
            "no_constraints": "명시적 제약을 찾지 못했습니다.",
            "citations": "컨텍스트 근거",
            "questions": "첫 실행 질문",
            "language": "언어/런타임 선택지",
            "method": "구현 방식 선택지",
            "existing": "기존 코드 처리 선택지",
            "validation": "검증 선택지",
            "documentation": "문서화 선택지",
            "advantages": "장점",
            "disadvantages": "단점",
            "when": "선택 기준",
        },
        "en": {
            "title": "Requirement packet",
            "summary": "Summary",
            "constraints": "Constraints",
            "no_constraints": "No explicit constraints detected.",
            "citations": "Context evidence",
            "questions": "First-run questions",
            "language": "Language/runtime options",
            "method": "Implementation method options",
            "existing": "Existing code options",
            "validation": "Validation options",
            "documentation": "Documentation options",
            "advantages": "Advantages",
            "disadvantages": "Disadvantages",
            "when": "When",
        },
    }
    labels = label_map.get(language, label_map["ko"])

    def render_localized_options(title: str, options: List[Option]) -> str:
        lines = [f"## {title}"]
        for option in options:
            lines.extend([
                f"### {option.name}",
                f"- {labels['advantages']}: {', '.join(option.advantages)}",
                f"- {labels['disadvantages']}: {', '.join(option.disadvantages)}",
                f"- {labels['when']}: {option.when_to_choose}",
            ])
        return "\n".join(lines)

    context = packet.context_summary
    citation_items: List[str] = []
    for key in ("docs", "build_files", "tests", "data_files", "source_files_sample"):
        values = context.get(key, [])
        if isinstance(values, list) and values:
            citation_items.append(f"- {key}: " + ", ".join(str(item) for item in values[:8]))
    citations = "\n".join(citation_items or ["- No inventory file evidence available."])

    sections = [
        f"# {labels['title']}",
        f"## {labels['summary']}\n\n{packet.prompt_summary}",
        f"## {labels['constraints']}\n\n" + "\n".join(f"- {c}" for c in packet.constraints or [labels["no_constraints"]]),
        f"## {labels['citations']}\n\n{citations}",
        render_localized_options(labels["language"], packet.language_options),
        render_localized_options(labels["method"], packet.method_options),
        render_localized_options(labels["existing"], packet.existing_code_options),
        render_localized_options(labels["validation"], packet.validation_options),
        render_localized_options(labels["documentation"], packet.documentation_options),
    ]
    if packet.open_questions:
        sections.append(f"## {labels['questions']}\n\n" + "\n".join(f"{i+1}. {q}" for i, q in enumerate(packet.open_questions)))
    return "\n\n".join(sections)


def packet_to_dict(packet: RequirementPacket) -> Dict[str, object]:
    """Convert packet dataclasses into plain dictionaries."""

    return asdict(packet)


def main() -> None:
    """CLI entrypoint for drafting a requirement packet."""

    parser = argparse.ArgumentParser(description="Analyze requirements for review-driven-development.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--prompt", default="")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    packet = create_requirement_packet(args.prompt, Path(args.root).resolve())
    if args.json:
        print(json.dumps(packet_to_dict(packet), ensure_ascii=False, indent=2))
    else:
        print(render_packet_markdown(packet))


if __name__ == "__main__":
    main()
