from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT / "skills" / "review-driven-development"
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import context_inventory as ci  # noqa: E402
from quality_gate import run_quality_gate  # noqa: E402
from context_inventory import BOOTSTRAP_BEGIN, build_inventory, load_context_pack, load_semantic_index, search_semantic_index, sklearn_available, sync_context  # noqa: E402
from subagent_brief_builder import role_list_for_phase, write_briefs  # noqa: E402
from todo_manager import (  # noqa: E402
    add_review_record,
    add_validation_evidence,
    complete_todo_if_ready,
    create_todo,
    get_todo,
    update_documentation_status,
)
from workflow_runner import run_bootstrap_phase, run_commands_phase, run_overview_phase, run_semantic_index_phase, run_semantic_search_phase, run_sync_phase  # noqa: E402


def run_cmd(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run([sys.executable, *args], cwd=REPO_ROOT, text=True, capture_output=True, check=True)


def test_skill_layout_and_scripts_compile() -> None:
    run_cmd("-m", "compileall", "-q", "skills/review-driven-development/scripts")
    out = run_cmd("skills/review-driven-development/scripts/validate_skill.py", "--skill-dir", str(SKILL_DIR)).stdout
    assert "ok: `True`" in out


def test_end_to_end_self_test() -> None:
    out = run_cmd("skills/review-driven-development/scripts/self_test.py").stdout
    payload = json.loads(out)
    assert payload["ok"] is True
    assert payload["validation_briefs"] >= 1
    assert payload["improvement_briefs"] >= 1


def test_registration_helper_validate_only() -> None:
    out = run_cmd("skills/review-driven-development/scripts/skill_registration.py", "--repo-root", str(REPO_ROOT), "--validate-only").stdout
    assert "VALID:" in out


def prepare_completable_todo(root: Path) -> str:
    todo = create_todo(root, "Harden completion gate", acceptance_criteria=["gate checked"])
    todo_id = todo["todo_id"]
    add_validation_evidence(root, todo_id, "manual validation evidence")
    add_review_record(root, todo_id, summary="independent review completed")
    update_documentation_status(root, todo_id, "updated", targets=["README.md"])
    return todo_id


def test_context_sync_writes_reusable_cache_and_pack() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "README.md").write_text("# Demo\n\nImportant project context.\n", encoding="utf-8")
        (root / "pyproject.toml").write_text("[tool.pytest.ini_options]\n", encoding="utf-8")
        (root / "app.py").write_text("class DemoService:\n    def run_demo(self):\n        print('ok')\n", encoding="utf-8")

        first = sync_context(root)
        second = sync_context(root)

        assert first["cache_hit"] is False
        assert second["cache_hit"] is True
        assert Path(first["inventory_path"]).exists()
        assert Path(first["cache_path"]).exists()
        assert Path(first["context_pack_path"]).exists()
        pack = load_context_pack(root)
        index = load_semantic_index(root)
        assert pack is not None
        assert index is not None
        assert "review-driven-development context pack" in pack
        assert "`README.md`" in pack
        assert any(symbol["name"] == "DemoService" for symbol in index["symbols"])
        assert first["context_inventory"]["semantic_index_summary"]["strategy"] in {"bounded-tfidf-symbol-index", "bounded-lexical-symbol-index"}
        assert first["context_inventory"]["semantic_index_summary"]["ranking_backend"] in {"sklearn-tfidf", "lexical-overlap"}
        search = search_semantic_index("demo service run", index, top_k=3)
        assert search["results"][0]["path"] == "app.py"
        assert search["ranking_backend"] == ("sklearn-tfidf" if sklearn_available() else "lexical-overlap")
        fallback = search_semantic_index("demo service run", index, top_k=3, force_fallback=True)
        assert fallback["ranking_backend"] == "lexical-overlap"
        assert fallback["results"][0]["path"] == "app.py"


def test_context_inventory_standard_mode_is_compact_by_default() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "README.md").write_text("# Demo\n\n" + "docs\n" * 400, encoding="utf-8")
        (root / "pyproject.toml").write_text("[project]\nname='demo'\n", encoding="utf-8")
        (root / "src").mkdir()
        (root / "src" / "app.py").write_text("def main():\n    return 'ok'\n", encoding="utf-8")
        (root / "tests").mkdir()
        (root / "tests" / "test_app.py").write_text("def test_app():\n    assert True\n", encoding="utf-8")

        inventory = build_inventory(root, mode="standard")

    assert inventory["inventory_mode"] == "standard"
    assert "doc_snippets" not in inventory
    assert inventory["limits"]["max_files"] == 1500
    assert inventory["limits"]["source_files_sample"] < 500
    assert inventory["docs"][0] == "README.md"
    assert inventory["has_existing_code"] is True
    assert inventory["has_tests"] is True


def test_rule_gated_subagent_selection_avoids_exhaustive_defaults() -> None:
    inventory = {
        "has_existing_code": True,
        "has_tests": True,
        "requires_data_critic": False,
        "needs_security_critic": False,
        "frameworks": [],
        "docs": ["README.md"],
        "source_files_sample": ["src/app.py"],
    }

    standard_roles = role_list_for_phase("preplan", inventory, critic_depth="standard")
    deep_with_data = role_list_for_phase(
        "preplan",
        {**inventory, "requires_data_critic": True, "data_files": ["data/sample.csv"]},
        critic_depth="deep",
    )

    assert 1 <= len(standard_roles) <= 4
    assert "requirements-critic" in standard_roles
    assert "data-csv-critic" not in standard_roles
    assert "data-csv-critic" in deep_with_data


def test_write_briefs_can_cap_roles_and_context_size() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        paths = write_briefs(
            root,
            "validation",
            "RDD-T-00000001",
            "x" * 5000,
            critic_depth="minimal",
            max_roles=1,
            context_max_chars=80,
        )
        text = paths[0].read_text(encoding="utf-8")

    assert len(paths) == 1
    assert "[truncated for token budget]" in text


def test_embedding_semantic_search_backend_can_rank_without_real_model(monkeypatch: pytest.MonkeyPatch) -> None:
    def fake_available() -> bool:
        return True

    def fake_encode(texts: list[str], *, model_name: str = "fake-model") -> dict[str, object]:
        vectors = []
        for text in texts:
            lowered = text.lower()
            vectors.append([1.0, 0.0] if "payment" in lowered or "billing" in lowered else [0.0, 1.0])
        return {"model": model_name, "dimension": 2, "vectors": vectors}

    monkeypatch.setattr(ci, "sentence_transformers_available", fake_available)
    monkeypatch.setattr(ci, "encode_embedding_texts", fake_encode)

    index = {
        "schema_version": 1,
        "ranking_backend": "embedding-cosine",
        "files": [
            {"path": "billing.py", "terms": ["billing"], "symbols": [], "search_text": "payment billing invoice"},
            {"path": "auth.py", "terms": ["auth"], "symbols": [], "search_text": "login token session"},
        ],
        "embedding": {"model": "fake-model", "vectors": [[1.0, 0.0], [0.0, 1.0]], "dimension": 2},
    }

    result = ci.search_semantic_index("payment problem", index, embedding_model="fake-model")
    assert result["ranking_backend"] == "embedding-cosine"
    assert result["results"][0]["path"] == "billing.py"


def test_workflow_runner_exposes_sync_overview_and_commands() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        (root / "README.md").write_text("# Demo\n", encoding="utf-8")

        sync = run_sync_phase(root)
        overview = run_overview_phase(root)
        semantic = run_semantic_index_phase(root)
        search = run_semantic_search_phase(root, "readme demo", top_k=3)
        bootstrap = run_bootstrap_phase(root)
        commands = run_commands_phase(root, "RDD-T-00000001")

        assert sync["phase"] == "sync"
        assert Path(str(sync["context_pack_path"])).exists()
        assert overview["phase"] == "overview"
        assert "context pack" in str(overview["context_pack"])
        assert semantic["phase"] == "semantic-index"
        assert Path(str(semantic["semantic_index_path"])).exists()
        assert search["phase"] == "semantic-search"
        assert search["search"]["results"]
        assert bootstrap["phase"] == "bootstrap"
        assert BOOTSTRAP_BEGIN in (root / "AGENTS.md").read_text(encoding="utf-8")
        assert commands["phase"] == "commands"
        assert any("--phase overview" in item for item in commands["context"])
        assert any("--phase semantic-search" in item for item in commands["context"])
        assert any("--phase bootstrap" in item for item in commands["context"])
        assert "RDD-T-00000001" in commands["quality"]["execute_current_todo"]


def test_dry_run_quality_gate_does_not_complete_when_commands_exist() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        todo = create_todo(root, "Run real gate", acceptance_criteria=["real command passes"])
        todo_id = todo["todo_id"]
        state_dir = root / ".codex" / "review-driven-development"
        state_dir.mkdir(parents=True, exist_ok=True)
        (state_dir / "commands.json").write_text(json.dumps({"test": ["python -c \"print('ok')\""], "lint": [], "build": [], "eval": []}), encoding="utf-8")

        run_quality_gate(root, todo_id, ["test"], execute=False, timeout=30, record_todo_evidence=True)
        add_review_record(root, todo_id, summary="independent review completed")
        update_documentation_status(root, todo_id, "updated", targets=["README.md"])

        with pytest.raises(RuntimeError, match="configured quality-gate commands require executed passing quality_gate evidence"):
            complete_todo_if_ready(root, todo_id)

        run_quality_gate(root, todo_id, ["test"], execute=True, timeout=30, record_todo_evidence=True)
        complete_todo_if_ready(root, todo_id)
        assert get_todo(root, todo_id)["status"] == "completed"


def test_unresolved_blocker_or_high_review_finding_blocks_completion() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        todo_id = prepare_completable_todo(root)
        add_review_record(root, todo_id, findings=[{
            "severity": "high",
            "claim": "Regression risk unresolved",
            "recommendation": "Add proof before completion",
        }])

        with pytest.raises(RuntimeError, match="unresolved blocker/high review findings"):
            complete_todo_if_ready(root, todo_id)


@pytest.mark.parametrize("decision", ["resolved", "reject", "rejected", "defer", "deferred"])
def test_resolved_rejected_or_deferred_blocker_high_review_finding_allows_completion(decision: str) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        todo_id = prepare_completable_todo(root)
        add_review_record(root, todo_id, findings=[{
            "severity": "blocker",
            "claim": "Concern handled by main agent decision",
            "decision": decision,
        }])

        complete_todo_if_ready(root, todo_id)
        assert get_todo(root, todo_id)["status"] == "completed"


def test_external_skill_urls_are_consistent_offline() -> None:
    registry = json.loads((REPO_ROOT / "external-skills.json").read_text(encoding="utf-8"))
    external_skills = (SKILL_DIR / "references" / "external-skills.md").read_text(encoding="utf-8")
    external_links = (SKILL_DIR / "references" / "external-skill-links.md").read_text(encoding="utf-8")

    missing = [
        item["url"]
        for item in registry
        if item["url"] not in external_skills or item["url"] not in external_links
    ]
    assert missing == []
