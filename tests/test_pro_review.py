from __future__ import annotations

import tempfile
from pathlib import Path
import sys
import pytest

SKILL_DIR = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import pro_review  # noqa: E402
from pro_review import append_todos, build_packet, extract_json_object, run_review, write_context_files  # noqa: E402
from todo_manager import create_todo  # noqa: E402
from todo_manager import list_todos  # noqa: E402


def test_extract_json_object_accepts_fenced_payload() -> None:
    payload = extract_json_object(
        """Review notes.

```json
{"summary": "ok", "todos": [{"title": "Add validation", "risk": "high"}]}
```
"""
    )

    assert payload["summary"] == "ok"
    assert payload["todos"][0]["title"] == "Add validation"


def test_dry_run_writes_context_without_provider_call() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "README.md").write_text("# Demo\n\nSmall project.\n", encoding="utf-8")

        result = run_review(root, "Review this demo.", dry_run=True, add_todos=False)

        round_result = result["rounds"][0]
        assert result["dry_run"] is True
        assert round_result["provider_status"] == "dry-run"
        assert Path(round_result["files"]["context_md"]).exists()
        assert Path(round_result["files"]["context_yaml"]).exists()
        assert Path(round_result["files"]["prompt_md"]).exists()
        assert Path(round_result["files"]["project_structure_md"]).exists()
        assert list_todos(root) == {}


def test_recursive_review_count_is_limited_to_one_round() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "README.md").write_text("# Demo\n\nSmall project.\n", encoding="utf-8")

        result = run_review(root, "Final recursive review.", recursive=True, count=3, dry_run=True, add_todos=False)

        assert result["recursive"] is True
        assert result["requested_count"] == 3
        assert result["count_was_limited"] is True
        assert result["executed_rounds"] == 1


def test_recursive_live_review_requires_terminal_todo_backlog() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        create_todo(root, "Finish local work", rationale="Open backlog item.")

        with pytest.raises(RuntimeError, match="TODO replenishment"):
            run_review(root, "Final recursive review.", recursive=True, dry_run=False, add_todos=False)


def test_packet_reuses_rdd_structure_completeness_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "README.md").write_text("# Demo\n\nSmall project.\n", encoding="utf-8")
        (root / "app.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")

        packet = build_packet(root, "Review this demo.", inventory_mode="standard", max_records=10)
        with tempfile.TemporaryDirectory() as round_tmp:
            files = write_context_files(Path(round_tmp), packet, "Review this demo.")

        assert "project_structure_completeness" in packet
        assert packet["project_structure_completeness"]["data"]["completeness"]["score"] >= 0
        assert "project_structure_md" in files


def test_append_todos_skips_duplicate_titles() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        payload = {
            "todos": [
                {"title": "Add smoke coverage", "acceptance_criteria": ["pytest passes"]},
                {"title": "Add smoke coverage", "acceptance_criteria": ["pytest passes"]},
            ]
        }

        created = append_todos(root, payload, source="test-round", limit=10)

        assert len(created) == 1
        todos = list_todos(root)
        assert len(todos) == 1
        assert next(iter(todos.values()))["title"] == "Add smoke coverage"


def test_run_agbrowse_parses_json_with_poll_suffix(monkeypatch) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "context.md").write_text("# Context\n", encoding="utf-8")
        (root / "context.yaml").write_text("a: b\n", encoding="utf-8")
        files = {
            "context_md": str(root / "context.md"),
            "context_yaml": str(root / "context.yaml"),
        }

        class Result:
            returncode = 0
            stdout = '{"answerText":"```json\\n{\\"summary\\":\\"ok\\",\\"todos\\":[]}\\n```"}\n[poll] streaming\\u2026'
            stderr = ""

        def fake_run(*args, **kwargs):
            assert kwargs["encoding"] == "utf-8"
            assert kwargs["errors"] == "replace"
            return Result()

        monkeypatch.setattr(pro_review, "resolve_agbrowse", lambda: "agbrowse.cmd")
        monkeypatch.setattr(pro_review.subprocess, "run", fake_run)

        payload = pro_review.run_agbrowse(root, files, timeout=1, model="pro", effort="standard")

        assert payload["answerText"].startswith("```json")
        assert (root / "agbrowse-result.json").exists()
        assert (root / "response.md").exists()
