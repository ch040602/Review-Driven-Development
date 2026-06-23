from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
SCRIPTS_DIR = REPO_ROOT / "skills" / "review-driven-development" / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

from diff_budget import analyze_diff_text  # noqa: E402


def test_diff_budget_blocks_logic_without_tests() -> None:
    diff = """diff --git a/src/app.py b/src/app.py
--- a/src/app.py
+++ b/src/app.py
@@ -0,0 +1,5 @@
+class Added:
+    pass
+def run():
+    return 1
+VALUE = 2
"""

    report = analyze_diff_text(diff)

    assert report["metrics"]["touched_files"] == 1
    assert report["metrics"]["new_classes"] == 1
    assert "tests missing while logic files changed" in report["blockers"]


def test_diff_budget_warns_on_large_added_loc() -> None:
    additions = "\n".join("+x = 1" for _ in range(201))
    diff = f"""diff --git a/tests/test_big.py b/tests/test_big.py
--- a/tests/test_big.py
+++ b/tests/test_big.py
@@ -0,0 +1,201 @@
{additions}
"""

    report = analyze_diff_text(diff)

    assert report["metrics"]["added_loc"] == 201
    assert any("added LOC" in warning for warning in report["warnings"])
