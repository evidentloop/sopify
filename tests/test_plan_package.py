from __future__ import annotations

from pathlib import Path
import tempfile
import unittest

from sopify_contracts import PLAN_FILES_BY_LEVEL, inspect_plan_package


def _write_plan(plan_dir: Path, level: str) -> None:
    plan_dir.mkdir(parents=True, exist_ok=True)
    (plan_dir / "plan.md").write_text(
        f"---\nlevel: {level}\n---\n\n# Test plan\n",
        encoding="utf-8",
    )
    for filename in PLAN_FILES_BY_LEVEL.get(level, ())[1:]:
        (plan_dir / filename).write_text(f"# {filename}\n", encoding="utf-8")


class PlanPackageTests(unittest.TestCase):
    def test_all_supported_levels_have_exact_semantic_files(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            for level, files in PLAN_FILES_BY_LEVEL.items():
                with self.subTest(level=level):
                    plan_dir = Path(temp_dir) / level
                    _write_plan(plan_dir, level)

                    snapshot = inspect_plan_package(plan_dir)

                    self.assertTrue(snapshot.valid)
                    self.assertEqual(snapshot.level, level)
                    self.assertEqual(snapshot.files, files)
                    self.assertRegex(snapshot.version or "", r"^sha256:[0-9a-f]{64}$")

    def test_missing_or_extra_semantic_file_is_invalid(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            missing_dir = Path(temp_dir) / "missing"
            _write_plan(missing_dir, "standard")
            (missing_dir / "tasks.md").unlink()
            self.assertFalse(inspect_plan_package(missing_dir).valid)

            extra_dir = Path(temp_dir) / "extra"
            _write_plan(extra_dir, "light")
            (extra_dir / "background.md").write_text("legacy", encoding="utf-8")
            self.assertFalse(inspect_plan_package(extra_dir).valid)

    def test_semantic_content_changes_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_dir = Path(temp_dir) / "plan"
            _write_plan(plan_dir, "architecture")
            initial = inspect_plan_package(plan_dir).version

            (plan_dir / "tasks.md").write_text("# changed tasks\n", encoding="utf-8")
            tasks_changed = inspect_plan_package(plan_dir).version
            (plan_dir / "design.md").write_text("# changed design\n", encoding="utf-8")
            design_changed = inspect_plan_package(plan_dir).version

            self.assertNotEqual(initial, tasks_changed)
            self.assertNotEqual(tasks_changed, design_changed)

    def test_derived_artifacts_do_not_change_version(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_dir = Path(temp_dir) / "plan"
            _write_plan(plan_dir, "architecture")
            initial = inspect_plan_package(plan_dir).version

            for relative_path in (
                "audits/plan/audit.json",
                "receipts/verify_001.json",
                "assets/note.txt",
            ):
                path = plan_dir / relative_path
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(relative_path, encoding="utf-8")

            self.assertEqual(inspect_plan_package(plan_dir).version, initial)

    def test_level_is_required_in_frontmatter(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            plan_dir = Path(temp_dir) / "plan"
            plan_dir.mkdir()
            (plan_dir / "plan.md").write_text("# no frontmatter\n", encoding="utf-8")

            snapshot = inspect_plan_package(plan_dir)

            self.assertFalse(snapshot.valid)
            self.assertIn("frontmatter", snapshot.error or "")


if __name__ == "__main__":
    unittest.main()
