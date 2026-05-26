# Test classification: contract
from __future__ import annotations

from tests.runtime_test_support import *
from runtime.plan.intent import request_explicitly_wants_new_plan


class PlanIntentTests(unittest.TestCase):
    def test_explicit_new_plan_patterns_ignore_ambiguous_other_plan_phrase(self) -> None:
        self.assertFalse(request_explicitly_wants_new_plan("分析这个方案和其他 plan 的差异"))
        self.assertTrue(request_explicitly_wants_new_plan("请新建一个 plan 处理这个问题"))

    def test_explicit_new_plan_patterns_respect_local_negation_without_global_blocking(self) -> None:
        self.assertFalse(request_explicitly_wants_new_plan("不要新建新的 plan 包，直接在当前 plan 上继续细化"))
        self.assertTrue(request_explicitly_wants_new_plan("不要复用当前 plan，直接新建 plan"))
        self.assertTrue(request_explicitly_wants_new_plan("不是不要新建 plan，而是要新建 plan"))
        self.assertTrue(request_explicitly_wants_new_plan("do not create a new plan; create a new plan now"))

    def test_empty_input_returns_false(self) -> None:
        self.assertFalse(request_explicitly_wants_new_plan(""))
        self.assertFalse(request_explicitly_wants_new_plan("   "))

    def test_chinese_new_plan_phrase_variants(self) -> None:
        self.assertTrue(request_explicitly_wants_new_plan("另起一个 plan 来做"))
        self.assertTrue(request_explicitly_wants_new_plan("新增 plan 处理这个需求"))
        self.assertFalse(request_explicitly_wants_new_plan("禁止新建 plan"))
