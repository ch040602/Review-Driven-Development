#!/usr/bin/env python3
"""ChatGPT Pro feedback loop for review-driven-development.

Builds a compact Markdown/YAML project packet, asks ChatGPT Pro through
agbrowse, stores the response, extracts TODO candidates, and optionally appends
them to the RDD TODO ledger.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, Mapping

try:
    from .constants import STATE_DIR, utc_stamp
    from .context_inventory import PROJECT_STRUCTURE_COMPLETENESS_JSON_FILE, PROJECT_STRUCTURE_COMPLETENESS_MD_FILE, sync_context
    from .todo_manager import create_todo, list_todos
except ImportError:  # pragma: no cover
    from constants import STATE_DIR, utc_stamp  # type: ignore
    from context_inventory import PROJECT_STRUCTURE_COMPLETENESS_JSON_FILE, PROJECT_STRUCTURE_COMPLETENESS_MD_FILE, sync_context  # type: ignore
    from todo_manager import create_todo, list_todos  # type: ignore


PRO_REVIEW_DIR = "pro-review"
TERMINAL_TODO_STATUSES = {"completed", "blocked", "deferred"}
DEFAULT_CHATGPT_URL = "https://chatgpt.com/"
PINNED_CHAT_GLOBAL_KEY = "__global__"
DEFAULT_PROMPT = (
    "Review the attached current implementation context. Return only actionable "
    "TODO feedback that should be added to the review-driven-development TODO ledger."
)
SYSTEM_PROMPT = """You are an external senior implementation reviewer.

Use only the attached Markdown/YAML context as evidence. Be critical but concise.
Do not propose broad rewrites unless the context proves they are necessary.
Prefer TODOs that are independently verifiable.

Return a single fenced JSON block with this schema:
{
  "summary": "1-3 sentence review summary",
  "todos": [
    {
      "title": "imperative TODO title",
      "rationale": "why this matters",
      "risk": "blocker|high|medium|low",
      "acceptance_criteria": ["observable check"],
      "expected_files": ["likely/path.ext"],
      "source_refs": ["context section or file path"]
    }
  ]
}
"""
AGBROWSE_SYSTEM_PROMPT = (
    "You are an external senior implementation reviewer. Use only the attached "
    "context as evidence and return only the requested JSON. For FLUX DERBY, "
    "the final objective is a Steam-releaseable Unity 2D pixel-art game, not a "
    "console or WinForms app. Do not propose real-money payment, cash-out, "
    "prizes, user trading, gambling-site integration, real horse-racing data, "
    "or actual betting advice."
)
AGBROWSE_USER_PROMPT = """Review the attached context.md and context.yaml.

Return a single fenced JSON block with these keys:
- summary: 1-3 sentence review summary.
- todos: array of actionable TODO objects.
- external_or_manual_todos: array of TODO objects that require Unity Editor,
  Steamworks, external downloads, credentials, rendered capture, hardware QA,
  legal review, or manual playtest evidence.

Each TODO object must include title, rationale, risk, acceptance_criteria,
expected_files, and source_refs. Use risk values blocker, high, medium, or low.
Put only locally executable TODOs in todos. Locally executable means no Unity
Editor, Steamworks access, external asset downloads, credentials, rendered
capture, hardware/device QA, legal review, or manual playtest is required.
Return an empty todos array when the context does not prove a concrete issue.
"""


def resolve_agbrowse() -> str:
    for candidate in ("agbrowse.cmd", "agbrowse.exe", "agbrowse"):
        path = shutil.which(candidate)
        if path:
            return path
    raise RuntimeError("agbrowse executable was not found on PATH. Run `npm install -g agbrowse` first.")


def run_git(root: Path, *args: str) -> str:
    """Return git command output, or a diagnostic string if unavailable."""

    result = subprocess.run(
        ["git", *args],
        cwd=root,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    output = (result.stdout or result.stderr).strip()
    return output if output else "(no output)"


def state_dir(root: Path) -> Path:
    directory = root / STATE_DIR / PRO_REVIEW_DIR
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def round_dir(root: Path, round_index: int) -> Path:
    directory = state_dir(root) / f"{utc_stamp()}-round-{round_index:03d}"
    directory.mkdir(parents=True, exist_ok=True)
    return directory


def scalar_yaml(value: Any) -> str:
    """Render a small YAML scalar without external dependencies."""

    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def to_yaml(value: Any, indent: int = 0) -> str:
    """Render simple dict/list/scalar data as YAML."""

    prefix = " " * indent
    if isinstance(value, Mapping):
        lines: list[str] = []
        for key, item in value.items():
            if isinstance(item, (Mapping, list)):
                lines.append(f"{prefix}{key}:")
                lines.append(to_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}{key}: {scalar_yaml(item)}")
        return "\n".join(lines)
    if isinstance(value, list):
        if not value:
            return f"{prefix}[]"
        lines = []
        for item in value:
            if isinstance(item, Mapping):
                lines.append(f"{prefix}-")
                lines.append(to_yaml(item, indent + 2))
            elif isinstance(item, list):
                lines.append(f"{prefix}-")
                lines.append(to_yaml(item, indent + 2))
            else:
                lines.append(f"{prefix}- {scalar_yaml(item)}")
        return "\n".join(lines)
    return f"{prefix}{scalar_yaml(value)}"


def trim_records(records: Any, limit: int) -> Any:
    if isinstance(records, list):
        return records[:limit]
    return records


def current_todo_summary(root: Path) -> list[dict[str, Any]]:
    todos = list_todos(root)
    summary = []
    for todo_id, todo in sorted(todos.items()):
        summary.append(
            {
                "todo_id": todo_id,
                "status": todo.get("status"),
                "risk": todo.get("risk"),
                "title": todo.get("title"),
                "acceptance_criteria": todo.get("acceptance_criteria", []),
            }
        )
    return summary


def open_todos(root: Path) -> list[dict[str, Any]]:
    """Return TODOs that are not in a terminal state."""

    open_items: list[dict[str, Any]] = []
    for todo_id, todo in sorted(list_todos(root).items()):
        status = str(todo.get("status") or "pending")
        if status in TERMINAL_TODO_STATUSES:
            continue
        open_items.append(
            {
                "todo_id": todo_id,
                "status": status,
                "title": todo.get("title", ""),
            }
        )
    return open_items


def codex_home() -> Path:
    configured = os.environ.get("CODEX_HOME")
    return Path(configured).expanduser() if configured else Path.home() / ".codex"


def pinned_chat_registry_path() -> Path:
    return codex_home() / "state" / "agbrowse-chatgpt-pro-review" / "chatgpt-session-registry.json"


def load_pinned_chat_registry() -> dict[str, dict[str, str]]:
    path = pinned_chat_registry_path()
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        return {}


def save_pinned_chat_registry(registry: Mapping[str, Mapping[str, str]]) -> None:
    path = pinned_chat_registry_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(registry, ensure_ascii=False, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def pinned_chat_url() -> str:
    entry = load_pinned_chat_registry().get(PINNED_CHAT_GLOBAL_KEY, {})
    url = str(entry.get("url") or "")
    return url if url.startswith("https://chatgpt.com/c/") else DEFAULT_CHATGPT_URL


def find_chatgpt_conversation_url(value: Any) -> str | None:
    if isinstance(value, str) and value.startswith("https://chatgpt.com/c/"):
        return value
    if isinstance(value, Mapping):
        for item in value.values():
            found = find_chatgpt_conversation_url(item)
            if found:
                return found
    if isinstance(value, list):
        for item in value:
            found = find_chatgpt_conversation_url(item)
            if found:
                return found
    return None


def persist_pinned_chat_url(url: str) -> None:
    if not url.startswith("https://chatgpt.com/c/"):
        return
    registry = load_pinned_chat_registry()
    previous = registry.get(PINNED_CHAT_GLOBAL_KEY, {})
    stamp = utc_stamp()
    registry[PINNED_CHAT_GLOBAL_KEY] = {
        "scope": "global",
        "workspace": "",
        "url": url,
        "createdAt": previous.get("createdAt", stamp),
        "lastUsedAt": stamp,
    }
    save_pinned_chat_registry(registry)


def touch_pinned_chat_url() -> None:
    registry = load_pinned_chat_registry()
    entry = registry.get(PINNED_CHAT_GLOBAL_KEY)
    if not entry:
        return
    entry["lastUsedAt"] = utc_stamp()
    save_pinned_chat_registry(registry)


def assert_pro_review_replenishment_allowed(root: Path, *, dry_run: bool) -> list[dict[str, Any]]:
    """Allow live Pro review only when it is time to replenish TODOs."""

    open_items = open_todos(root)
    if open_items and not dry_run:
        compact = ", ".join(f"{item['todo_id']}:{item['status']}" for item in open_items[:10])
        raise RuntimeError(
            "ChatGPT Pro review is allowed only as a TODO replenishment step "
            "after all active RDD TODOs are completed, blocked, or deferred. "
            f"Open TODOs: {compact}"
        )
    return open_items


def assert_recursive_final_review_allowed(root: Path, *, dry_run: bool) -> list[dict[str, Any]]:
    """Allow live recursive Pro review only after the active TODO backlog is done."""

    open_items = open_todos(root)
    if open_items and not dry_run:
        compact = ", ".join(f"{item['todo_id']}:{item['status']}" for item in open_items[:10])
        raise RuntimeError(
            "Recursive ChatGPT Pro review is limited to one final pass after all "
            "active RDD TODOs are completed, blocked, or deferred. "
            f"Open TODOs: {compact}"
        )
    return open_items


def read_project_structure_packet(root: Path, sync: Mapping[str, Any]) -> dict[str, Any]:
    """Read the RDD structure/completeness files generated by context sync."""

    md_path = Path(str(sync.get("project_structure_md_path") or root / STATE_DIR / PROJECT_STRUCTURE_COMPLETENESS_MD_FILE))
    json_path = Path(str(sync.get("project_structure_json_path") or root / STATE_DIR / PROJECT_STRUCTURE_COMPLETENESS_JSON_FILE))
    packet: dict[str, Any] = {
        "markdown_path": str(md_path),
        "json_path": str(json_path),
        "markdown": "",
        "data": {},
    }
    if md_path.exists():
        packet["markdown"] = md_path.read_text(encoding="utf-8")
    if json_path.exists():
        try:
            packet["data"] = json.loads(json_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            packet["data"] = {}
    return packet


def read_release_evidence_digest(root: Path) -> dict[str, Any]:
    """Read the durable release evidence digest when the project exports one."""

    path = root / STATE_DIR / "release-evidence-digest.json"
    packet: dict[str, Any] = {
        "path": str(path),
        "data": {},
    }
    if path.exists():
        try:
            packet["data"] = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            packet["data"] = {}
    return packet


def build_packet(root: Path, prompt: str, *, inventory_mode: str, max_records: int) -> dict[str, Any]:
    sync = sync_context(root, mode=inventory_mode, include_snippets=False)
    inventory = sync["context_inventory"]
    project_structure = read_project_structure_packet(root, sync)
    release_evidence_digest = read_release_evidence_digest(root)
    return {
        "request": {
            "prompt": prompt,
            "reviewer": "chatgpt-pro-via-agbrowse",
            "expected_output": "JSON TODO candidates",
        },
        "project": {
            "root": str(root),
            "inventory_mode": inventory.get("inventory_mode"),
            "scanned_file_count": inventory.get("scanned_file_count"),
            "primary_languages": inventory.get("primary_languages", []),
            "frameworks": inventory.get("frameworks", []),
            "has_existing_code": inventory.get("has_existing_code"),
            "has_tests": inventory.get("has_tests"),
            "recommended_critics": inventory.get("recommended_critics", []),
        },
        "git": {
            "status": run_git(root, "status", "--short"),
            "diff_stat": run_git(root, "diff", "--stat"),
            "last_commit": run_git(root, "log", "-1", "--oneline"),
        },
        "files": {
            "build_files": trim_records(inventory.get("build_files", []), max_records),
            "tests": trim_records(inventory.get("tests", []), max_records),
            "docs": trim_records(inventory.get("docs", []), max_records),
            "data_files": trim_records(inventory.get("data_files", []), max_records),
            "source_files_sample": trim_records(inventory.get("source_files_sample", []), max_records),
            "role_map": trim_records(inventory.get("role_map", []), max_records),
        },
        "project_structure_completeness": {
            "markdown_path": project_structure["markdown_path"],
            "json_path": project_structure["json_path"],
            "data": project_structure["data"],
        },
        "release_evidence_digest": release_evidence_digest,
        "todos": current_todo_summary(root),
    }


def packet_markdown(packet: Mapping[str, Any]) -> str:
    lines = [
        "# ChatGPT Pro Review Context",
        "",
        "## Request",
        "",
        str(packet["request"]["prompt"]),
        "",
        "## Project",
        "",
        f"- root: `{packet['project']['root']}`",
        f"- inventory_mode: `{packet['project']['inventory_mode']}`",
        f"- scanned_file_count: `{packet['project']['scanned_file_count']}`",
        f"- primary_languages: `{', '.join(packet['project']['primary_languages'])}`",
        f"- frameworks: `{', '.join(packet['project']['frameworks']) or 'none'}`",
        f"- has_existing_code: `{packet['project']['has_existing_code']}`",
        f"- has_tests: `{packet['project']['has_tests']}`",
        "",
        "## Git",
        "",
        "### Status",
        "",
        "```text",
        packet["git"]["status"],
        "```",
        "",
        "### Diff Stat",
        "",
        "```text",
        packet["git"]["diff_stat"],
        "```",
        "",
        "## File Structure Summary",
        "",
    ]
    structure_packet = packet.get("project_structure_completeness", {})
    if isinstance(structure_packet, Mapping):
        structure_data = structure_packet.get("data", {})
        completeness = structure_data.get("completeness", {}) if isinstance(structure_data, Mapping) else {}
        lines.extend(
            [
                "## RDD Project Structure And Completeness",
                "",
                f"- markdown_path: `{structure_packet.get('markdown_path')}`",
                f"- json_path: `{structure_packet.get('json_path')}`",
                f"- completeness: `{completeness.get('score', 'unknown')}/100` `{completeness.get('label', 'unknown')}`",
                "",
                "Use the attached project-structure-completeness.md as the primary structure/role/completeness evidence.",
                "",
            ]
        )
    digest_packet = packet.get("release_evidence_digest", {})
    if isinstance(digest_packet, Mapping):
        digest_data = digest_packet.get("data", {})
        if isinstance(digest_data, Mapping) and digest_data:
            lines.extend(
                [
                    "## Release Evidence Digest",
                    "",
                    f"- path: `{digest_packet.get('path')}`",
                    f"- status: `{digest_data.get('status', 'unknown')}`",
                    f"- generated_at: `{digest_data.get('generated_at', 'unknown')}`",
                    "",
                    "| id | status | report_path | sha256 | source_command |",
                    "|---|---|---|---|---|",
                ]
            )
            for item in digest_data.get("reports", []):
                if isinstance(item, Mapping):
                    lines.append(
                        f"| `{item.get('id')}` | `{item.get('status')}` | `{item.get('report_path')}` | `{item.get('sha256')}` | `{item.get('source_command')}` |"
                    )
            lines.append("")
    for label, records in packet["files"].items():
        lines.extend([f"### {label}", ""])
        if not records:
            lines.append("- none")
        elif isinstance(records, list):
            for item in records:
                if isinstance(item, Mapping):
                    path = item.get("path") or item.get("file") or item.get("name") or json.dumps(item, ensure_ascii=False)
                    extra = item.get("role") or item.get("kind") or item.get("language") or ""
                    lines.append(f"- `{path}` {extra}".rstrip())
                else:
                    lines.append(f"- `{item}`")
        lines.append("")
    lines.extend(["## Current TODOs", ""])
    todos = packet.get("todos", [])
    if not todos:
        lines.append("- none")
    else:
        for todo in todos:
            lines.append(f"- `{todo.get('todo_id')}` `{todo.get('status')}` `{todo.get('risk')}` {todo.get('title')}")
    lines.append("")
    return "\n".join(lines)


def write_context_files(directory: Path, packet: Mapping[str, Any], prompt: str) -> dict[str, str]:
    context_md = directory / "context.md"
    context_yaml = directory / "context.yaml"
    prompt_md = directory / "prompt.md"
    context_md.write_text(packet_markdown(packet), encoding="utf-8", newline="\n")
    context_yaml.write_text(to_yaml(packet) + "\n", encoding="utf-8", newline="\n")
    prompt_md.write_text(SYSTEM_PROMPT + "\n\n" + prompt + "\n", encoding="utf-8", newline="\n")
    files = {
        "context_md": str(context_md),
        "context_yaml": str(context_yaml),
        "prompt_md": str(prompt_md),
    }
    structure_packet = packet.get("project_structure_completeness", {})
    if isinstance(structure_packet, Mapping):
        structure_md = Path(str(structure_packet.get("markdown_path", "")))
        if structure_md.exists():
            files["project_structure_md"] = str(structure_md)
    return files


def run_agbrowse(directory: Path, files: Mapping[str, str], *, timeout: int, model: str, effort: str) -> dict[str, Any]:
    review_url = pinned_chat_url()
    command = [
        resolve_agbrowse(),
        "web-ai",
        "query",
        "--vendor",
        "chatgpt",
        "--url",
        review_url,
        "--model",
        model,
        "--effort",
        effort,
        "--file",
        files["context_md"],
        "--file",
        files["context_yaml"],
    ]
    if files.get("project_structure_md"):
        command.extend(["--file", files["project_structure_md"]])
    command.extend([
        "--allow-copy-markdown-fallback",
        "--timeout",
        str(timeout),
        "--json",
        "--system",
        AGBROWSE_SYSTEM_PROMPT,
        "--prompt",
        AGBROWSE_USER_PROMPT,
    ])
    result = subprocess.run(
        command,
        cwd=directory,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    raw = {
        "command": command,
        "returncode": result.returncode,
        "stdout": result.stdout,
        "stderr": result.stderr,
    }
    (directory / "agbrowse-result.json").write_text(json.dumps(raw, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or "agbrowse web-ai query failed")
    payload_start = result.stdout.find("{")
    if payload_start < 0:
        raise RuntimeError("agbrowse returned no JSON payload")
    payload, _ = json.JSONDecoder().raw_decode(result.stdout[payload_start:])
    answer = payload.get("answerText") or payload.get("answerArtifact", {}).get("text") or ""
    (directory / "response.md").write_text(str(answer), encoding="utf-8", newline="\n")
    conversation_url = find_chatgpt_conversation_url(payload)
    if conversation_url:
        persist_pinned_chat_url(conversation_url)
    else:
        touch_pinned_chat_url()
    return payload


def extract_json_object(text: str) -> dict[str, Any]:
    fenced = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, flags=re.DOTALL | re.IGNORECASE)
    candidate = fenced.group(1) if fenced else text[text.find("{") : text.rfind("}") + 1]
    if not candidate.strip():
        return {"summary": "No JSON TODO payload found.", "todos": []}
    try:
        parsed = json.loads(candidate)
    except json.JSONDecodeError:
        return {"summary": "Could not parse JSON TODO payload.", "todos": []}
    if not isinstance(parsed, dict):
        return {"summary": "JSON payload was not an object.", "todos": []}
    if not isinstance(parsed.get("todos"), list) and isinstance(parsed.get("locally_executable_todos"), list):
        parsed["todos"] = parsed["locally_executable_todos"]
    if not isinstance(parsed.get("external_or_manual_todos"), list) and isinstance(parsed.get("external_manual_todos"), list):
        parsed["external_or_manual_todos"] = parsed["external_manual_todos"]
    todos = parsed.get("todos", [])
    if not isinstance(todos, list):
        parsed["todos"] = []
    return parsed


def normalize_risk(value: Any) -> str:
    value = str(value or "medium").strip().lower()
    return value if value in {"blocker", "high", "medium", "low"} else "medium"


def append_todos(root: Path, payload: Mapping[str, Any], *, source: str, limit: int) -> list[dict[str, Any]]:
    created = []
    existing_titles = {
        str(todo.get("title", "")).strip().lower()
        for todo in list_todos(root).values()
        if str(todo.get("title", "")).strip()
    }
    for item in list(payload.get("todos", []))[:limit]:
        if not isinstance(item, Mapping):
            continue
        title = str(item.get("title") or item.get("recommendation") or "").strip()
        normalized_title = title.lower()
        if not title or normalized_title in existing_titles:
            continue
        acceptance = item.get("acceptance_criteria") or item.get("acceptance") or []
        if isinstance(acceptance, str):
            acceptance = [acceptance]
        expected_files = item.get("expected_files") or []
        if isinstance(expected_files, str):
            expected_files = [expected_files]
        rationale = str(item.get("rationale") or item.get("risk") or "ChatGPT Pro review TODO candidate.")
        created.append(
            create_todo(
                root,
                title,
                rationale=f"{rationale}\n\nSource: {source}",
                risk=normalize_risk(item.get("risk")),
                acceptance_criteria=[str(entry) for entry in acceptance],
                expected_files=[str(entry) for entry in expected_files],
                source_finding_id=source,
            )
        )
        existing_titles.add(normalized_title)
    return created


def append_external_or_manual_todos(root: Path, payload: Mapping[str, Any], *, source: str, limit: int) -> list[dict[str, Any]]:
    remain_items = payload.get("external_or_manual_todos", [])
    if not isinstance(remain_items, list):
        return []
    remain_path = root / STATE_DIR / "todo_remain.jsonl"
    remain_path.parent.mkdir(parents=True, exist_ok=True)
    existing = remain_path.read_text(encoding="utf-8").splitlines() if remain_path.exists() else []
    start_index = len([line for line in existing if line.strip()]) + 1
    stamp = utc_stamp()
    created: list[dict[str, Any]] = []
    tag_keywords = {
        "unity_editor": ["unity editor", "unity test", "playmode", "editmode", "build"],
        "steamworks_access": ["steam", "steamworks", "valve", "depot", "store presence"],
        "external_asset_download": ["external asset", "download", "craftpix", "figma"],
        "credentials": ["credential", "login", "account", "secret"],
        "rendered_capture": ["rendered", "screenshot", "capture", "trailer"],
        "manual_qa": ["manual", "qa", "review", "sign off", "sign-off"],
        "external_playtest": ["playtest", "tester", "feedback"],
        "hardware_qa": ["hardware", "steam deck", "controller", "device"],
        "legal_review": ["legal", "license"],
    }
    for offset, item in enumerate(remain_items[:limit], start=start_index):
        if not isinstance(item, Mapping):
            continue
        acceptance = item.get("acceptance_criteria") or item.get("acceptance") or []
        if isinstance(acceptance, str):
            acceptance = [acceptance]
        text = " ".join([str(item.get("title", "")), str(item.get("dependency", "")), str(item.get("rationale", "")), " ".join(str(value) for value in acceptance)]).lower()
        dependency_tags = [tag for tag, keywords in tag_keywords.items() if any(keyword in text for keyword in keywords)]
        if not dependency_tags:
            dependency_tags = ["manual_qa"]
        entry = {
            "id": f"RDD-REM-PRO-{stamp}-{offset:03d}",
            "source_todo": source,
            "status": "deferred",
            "title": str(item.get("title") or item.get("recommendation") or "External/manual Pro review TODO").strip(),
            "reason": str(item.get("rationale") or "Requires external/manual dependency."),
            "required_dependency": str(
                item.get("required_dependency")
                or "Unity Editor, Steamworks, external download, credentials, rendered capture, hardware QA, legal review, or manual playtest evidence"
            ),
            "last_evidence": [str(value) for value in acceptance],
            "resume_command_or_action": str(item.get("resume_command_or_action") or "Resume when the required external/manual dependency is available."),
            "timestamp": stamp,
            "dependency_tags": dependency_tags,
        }
        created.append(entry)
    if created:
        with remain_path.open("a", encoding="utf-8", newline="\n") as handle:
            for entry in created:
                handle.write(json.dumps(entry, ensure_ascii=False) + "\n")
    return created


def run_round(
    root: Path,
    prompt: str,
    *,
    round_index: int,
    dry_run: bool,
    add_todos: bool,
    inventory_mode: str,
    max_records: int,
    todo_limit: int,
    timeout: int,
    model: str,
    effort: str,
) -> dict[str, Any]:
    directory = round_dir(root, round_index)
    packet = build_packet(root, prompt, inventory_mode=inventory_mode, max_records=max_records)
    files = write_context_files(directory, packet, prompt)
    if dry_run:
        payload = {"summary": "dry run; no provider call", "todos": []}
        provider = {"ok": False, "status": "dry-run"}
    else:
        provider = run_agbrowse(directory, files, timeout=timeout, model=model, effort=effort)
        answer = provider.get("answerText") or provider.get("answerArtifact", {}).get("text") or ""
        payload = extract_json_object(str(answer))
    (directory / "todo-candidates.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8", newline="\n")
    created = append_todos(root, payload, source=str(directory), limit=todo_limit) if add_todos and not dry_run else []
    external_created = (
        append_external_or_manual_todos(root, payload, source=str(directory), limit=todo_limit)
        if add_todos and not dry_run
        else []
    )
    return {
        "round": round_index,
        "directory": str(directory),
        "files": files,
        "provider_status": provider.get("status"),
        "provider_url": provider.get("url"),
        "candidate_count": len(payload.get("todos", [])),
        "external_or_manual_candidate_count": len(payload.get("external_or_manual_todos", []))
        if isinstance(payload.get("external_or_manual_todos"), list)
        else 0,
        "created_todos": created,
        "created_todo_remain": external_created,
    }


def run_review(
    root: Path,
    prompt: str,
    *,
    count: int = 1,
    recursive: bool = False,
    dry_run: bool = False,
    add_todos: bool = True,
    inventory_mode: str = "standard",
    max_records: int = 30,
    todo_limit: int = 10,
    timeout: int = 3600,
    model: str = "pro",
    effort: str = "standard",
) -> dict[str, Any]:
    open_items = assert_pro_review_replenishment_allowed(root, dry_run=dry_run)
    if recursive:
        assert_recursive_final_review_allowed(root, dry_run=dry_run)
    rounds = 1
    count_was_limited = bool(recursive and count != 1)
    results = []
    for index in range(1, rounds + 1):
        results.append(
            run_round(
                root,
                prompt,
                round_index=index,
                dry_run=dry_run,
                add_todos=add_todos,
                inventory_mode=inventory_mode,
                max_records=max_records,
                todo_limit=todo_limit,
                timeout=timeout,
                model=model,
                effort=effort,
            )
        )
    return {
        "phase": "pro-review",
        "recursive": recursive,
        "requested_count": count,
        "count_was_limited": count_was_limited,
        "executed_rounds": rounds,
        "open_todos_at_start": open_items,
        "add_todos": add_todos,
        "dry_run": dry_run,
        "rounds": results,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Ask ChatGPT Pro for RDD TODO feedback through agbrowse.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--prompt", default=DEFAULT_PROMPT)
    parser.add_argument("--count", type=int, default=1, help="Compatibility option; recursive review is limited to one live round")
    parser.add_argument("--recursive", action="store_true", help="Run the final-only one-shot recursive Pro review import")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--no-add-todos", action="store_true")
    parser.add_argument("--inventory-mode", choices=["fast", "standard", "deep"], default="standard")
    parser.add_argument("--max-records", type=int, default=30)
    parser.add_argument("--todo-limit", type=int, default=10)
    parser.add_argument("--timeout", type=int, default=3600)
    parser.add_argument("--model", default="pro")
    parser.add_argument("--effort", default="standard")
    args = parser.parse_args()
    result = run_review(
        Path(args.root).resolve(),
        args.prompt,
        count=args.count,
        recursive=args.recursive,
        dry_run=args.dry_run,
        add_todos=not args.no_add_todos,
        inventory_mode=args.inventory_mode,
        max_records=args.max_records,
        todo_limit=args.todo_limit,
        timeout=args.timeout,
        model=args.model,
        effort=args.effort,
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
