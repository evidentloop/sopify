from __future__ import annotations

from pathlib import Path
import json
import subprocess
import sys
import tempfile
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]


class PlanContractAssetTests(unittest.TestCase):
    def test_bilingual_sources_share_current_plan_levels(self) -> None:
        for language in ("zh", "en"):
            with self.subTest(language=language):
                language_root = REPO_ROOT / "skills" / language
                header = (language_root / "header.md.template").read_text(
                    encoding="utf-8"
                )
                design_rules = (
                    language_root
                    / "skills"
                    / "sopify"
                    / "design"
                    / "references"
                    / "design-rules.md"
                ).read_text(encoding="utf-8")
                templates = (
                    language_root / "skills" / "sopify" / "templates" / "SKILL.md"
                ).read_text(encoding="utf-8")

                for content in (header, design_rules, templates):
                    self.assertIn("light", content)
                    self.assertIn("standard", content)
                    self.assertIn("architecture", content)
                self.assertNotIn("light/standard/full", header)
                self.assertNotIn("background.md + design.md + tasks.md", design_rules)
                self.assertNotIn("Full Level", templates)
                self.assertNotIn("Full 级别", templates)

    def test_design_assets_match_the_three_level_file_contract(self) -> None:
        for language in ("zh", "en"):
            with self.subTest(language=language):
                assets = (
                    REPO_ROOT
                    / "skills"
                    / language
                    / "skills"
                    / "sopify"
                    / "design"
                    / "assets"
                )
                self.assertTrue((assets / "plan-template.md").is_file())
                self.assertTrue((assets / "tasks-template.md").is_file())
                self.assertTrue((assets / "design-template.md").is_file())
                self.assertFalse((assets / "plan-light-template.md").exists())
                self.assertFalse((assets / "background-template.md").exists())

    def test_bilingual_selectors_return_architecture(self) -> None:
        for language in ("zh", "en"):
            with self.subTest(language=language):
                script = (
                    REPO_ROOT
                    / "skills"
                    / language
                    / "skills"
                    / "sopify"
                    / "design"
                    / "scripts"
                    / "select_plan_level.py"
                )
                result = subprocess.run(
                    [sys.executable, str(script), "--file-count", "2", "--new-system"],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                self.assertEqual(
                    json.loads(result.stdout)["plan_level"], "architecture"
                )

    def test_rendered_host_headers_keep_the_same_contract(self) -> None:
        render_script = REPO_ROOT / "scripts" / "render-host-skills.py"
        for language in ("zh", "en"):
            for host in ("codex", "claude", "qoder", "copilot"):
                with (
                    self.subTest(language=language, host=host),
                    tempfile.TemporaryDirectory() as temp_dir,
                ):
                    output = Path(temp_dir) / "host.md"
                    subprocess.run(
                        [
                            sys.executable,
                            str(render_script),
                            "--hosts-file",
                            str(REPO_ROOT / "skills" / "hosts.yaml"),
                            "--skills-root",
                            str(REPO_ROOT / "skills"),
                            "--lang",
                            language,
                            "--host",
                            host,
                            "--output",
                            str(output),
                        ],
                        check=True,
                        capture_output=True,
                        text=True,
                    )
                    rendered = output.read_text(encoding="utf-8")
                    self.assertIn("plan_version", rendered)
                    self.assertIn("architecture", rendered)
                    self.assertNotIn("light/standard/full", rendered)


if __name__ == "__main__":
    unittest.main()
