# Test classification: contract
from __future__ import annotations

from tests.runtime_test_support import *
from runtime.plan.lookup import (
    find_plan_by_request_reference,
    find_plan_by_topic_key,
    load_plan_artifact,
)


class PlanLookupTests(unittest.TestCase):
    def test_find_plan_by_topic_key_returns_matching_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)

            artifact = create_plan_scaffold("补 runtime 骨架", config=config, level="standard")

            found = find_plan_by_topic_key(artifact.topic_key, config=config)
            self.assertIsNotNone(found)
            assert found is not None
            self.assertEqual(found.plan_id, artifact.plan_id)
            self.assertEqual(found.topic_key, artifact.topic_key)

    def test_find_plan_by_topic_key_returns_none_for_missing(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)

            found = find_plan_by_topic_key("nonexistent-topic", config=config)
            self.assertIsNone(found)

    def test_load_plan_artifact_reconstructs_from_disk(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir).resolve()
            config = load_runtime_config(workspace)

            artifact = create_plan_scaffold("实现 runtime skeleton", config=config, level="standard")

            loaded = load_plan_artifact(workspace / artifact.path, config=config)
            self.assertIsNotNone(loaded)
            assert loaded is not None
            self.assertEqual(loaded.plan_id, artifact.plan_id)
            self.assertIn(artifact.title, loaded.title)
            self.assertEqual(loaded.topic_key, artifact.topic_key)

    def test_find_plan_by_request_reference_extracts_plan_id(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)

            artifact = create_plan_scaffold("补 runtime 骨架", config=config, level="standard")

            found = find_plan_by_request_reference(
                f"请查看 plan:{artifact.plan_id} 的进展",
                config=config,
            )
            self.assertIsNotNone(found)
            assert found is not None
            self.assertEqual(found.plan_id, artifact.plan_id)

    def test_find_plan_by_request_reference_returns_none_for_no_match(self) -> None:
        with tempfile.TemporaryDirectory() as temp_dir:
            workspace = Path(temp_dir)
            config = load_runtime_config(workspace)

            found = find_plan_by_request_reference("没有任何引用", config=config)
            self.assertIsNone(found)
