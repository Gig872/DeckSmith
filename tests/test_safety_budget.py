# -*- coding: utf-8 -*-
import unittest

from config import Settings
from safety import Guard, classify_goal, GOAL_TIERS


class TestClassifyGoal(unittest.TestCase):
    def test_minimal_is_S(self):
        self.assertEqual(classify_goal("请用单一控制体 snglvol 建一个最小可跑模型"), "S")

    def test_empty_is_M(self):
        self.assertEqual(classify_goal(""), "M")

    def test_complex_is_high(self):
        self.assertIn(classify_goal(
            "搭一个完整的一二回路整体式压水堆瞬态模型，含稳压器、蒸汽发生器、点堆、安注、控制系统"),
            ("L", "XL"))

    def test_batch_keywords_boost(self):
        # "批量" 会把起档抬高（不再是被当作最小）
        self.assertIn(classify_goal("帮我做一批仿真，看看参数影响"), ("M", "L", "XL"))


class TestBudgetGrowth(unittest.TestCase):
    def setUp(self):
        self.s = Settings()

    def test_no_grow_without_progress(self):
        g = Guard(self.s, goal="最小 snglvol 模型")   # S 档
        self.assertEqual(g.budget.tier, "S")
        self.assertEqual(g.maybe_grow(24), "")         # 已接近步数上限、但无进展 → 不放宽

    def test_grow_with_progress(self):
        g = Guard(self.s, goal="最小 snglvol 模型")
        g.observe(30, "parse_output", "正常结束=True  错误数=0")  # 制造真实进展
        note = g.maybe_grow(31)
        self.assertTrue(note)                           # 有进展 + 接近上限 → 放宽
        self.assertGreater(g.budget.cur["steps"], GOAL_TIERS["S"]["steps"])

    def test_hard_ceiling_not_exceeded(self):
        g = Guard(self.s, goal="最小 snglvol 模型")
        g.budget.cur["steps"] = g.budget.hard["steps"] - 1
        g.budget.ever_progress = True
        g.budget.last_progress_step = 100
        g.budget._last_up_step = 0
        g.budget.ups = 0
        g.maybe_grow(100)
        self.assertLessEqual(g.budget.cur["steps"], g.budget.hard["steps"])

    def test_freeze_when_unhealthy(self):
        g = Guard(self.s, goal="最小 snglvol 模型")
        g.observe(30, "parse_output", "错误数=0")
        g._healthy = False
        self.assertEqual(g.maybe_grow(31), "")


if __name__ == "__main__":
    unittest.main()
