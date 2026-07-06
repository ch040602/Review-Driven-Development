from __future__ import annotations

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SKILL_DIR = REPO_ROOT if (REPO_ROOT / "SKILL.md").exists() else REPO_ROOT / "skills" / "review-driven-development"
SCRIPTS_DIR = SKILL_DIR / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from minimal_solution_ladder import build_minimality_packet, save_minimality_packet  # noqa: E402


def test_minimal_ladder_prefers_existing_code_reuse_and_writes_packet(tmp_path: Path) -> None:
    scripts = tmp_path / "skills" / "review-driven-development" / "scripts"
    scripts.mkdir(parents=True)
    (scripts / "context_inventory.py").write_text("def build_context_pack(data):\n    return 'pack'\n", encoding="utf-8")

    packet = build_minimality_packet(
        tmp_path,
        "Add role-map output to context inventory instead of building a second scanner",
        todo_id="RDD-T-00000003",
    )
    path = save_minimality_packet(tmp_path, packet)

    assert packet["todo_id"] == "RDD-T-00000003"
    assert packet["rung"] == "reuse_existing_code"
    assert "context_inventory.py" in packet["decision"]
    assert "new dependency" in packet["skipped"]
    assert json.loads(path.read_text(encoding="utf-8"))["rung"] == "reuse_existing_code"


def test_minimal_ladder_flags_unnecessary_requirement_as_skip(tmp_path: Path) -> None:
    packet = build_minimality_packet(tmp_path, "Do we really need a new plugin system?")

    assert packet["rung"] == "skip"
    assert "Only add work after a concrete acceptance criterion exists." in packet["add_when"]
