# -*- coding: utf-8 -*-
import unittest

from postprocess.plot import chart_spec


class TestChartSpec(unittest.TestCase):
    def test_basic(self):
        spec = chart_spec({"a": [(0, 1), (1, 3)], "b": [(0, 2), (1, 2)]})
        self.assertEqual(len(spec["lines"]), 2)
        self.assertEqual(spec["xrange"], (0.0, 1.0))
        self.assertLess(spec["yrange"][0], 1.0)      # 留了下边距
        self.assertGreater(spec["yrange"][1], 3.0)   # 留了上边距

    def test_empty(self):
        self.assertIsNone(chart_spec({}))
        self.assertIsNone(chart_spec({"a": []}))

    def test_single_point(self):
        spec = chart_spec({"a": [(5, 5)]})
        self.assertEqual(len(spec["lines"]), 1)
        self.assertEqual(spec["xrange"][0], 5)

    def test_flat_line_range_ok(self):
        spec = chart_spec({"a": [(0, 2), (1, 2)]})   # y 全相等 → 仍需有效范围
        self.assertLess(spec["yrange"][0], spec["yrange"][1])


if __name__ == "__main__":
    unittest.main()
