# -*- coding: utf-8 -*-
import unittest

from postprocess.features import curve_features, format_features


class TestCurveFeatures(unittest.TestCase):
    def test_rising(self):
        f = curve_features({"v": [(0, 0), (1, 1), (2, 2)]})[0]
        self.assertEqual(f["trend"], "总体上升")
        self.assertEqual(f["max"], 2)
        self.assertEqual(f["t_max"], 2)
        self.assertEqual(f["min"], 0)
        self.assertAlmostEqual(f["delta"], 2)

    def test_falling(self):
        f = curve_features({"v": [(0, 3), (1, 2), (2, 1)]})[0]
        self.assertEqual(f["trend"], "总体下降")

    def test_flat(self):
        f = curve_features({"v": [(0, 5), (1, 5), (2, 5)]})[0]
        self.assertEqual(f["trend"], "平稳")

    def test_oscillating(self):
        ys = [(0, 0), (1, 5), (2, 0), (3, 5), (4, 0), (5, 5), (6, 0), (7, 5), (8, 0)]
        f = curve_features({"v": ys})[0]
        self.assertIn(f["trend"], ("振荡", "先升后降"))

    def test_plateau(self):
        ys = [(i, 1.0 + i) for i in range(10)] + [(10 + i, 11.0) for i in range(5)]
        f = curve_features({"v": ys})[0]
        self.assertIsNotNone(f["plateau"])
        self.assertAlmostEqual(f["plateau"], 11.0, places=6)

    def test_threshold_cross(self):
        f = curve_features({"v": [(0, 0.2), (1, 0.5), (2, 1.5), (3, 1.7)]}, thr=0.99)[0]
        self.assertIsNotNone(f["cross"])
        self.assertEqual(f["cross"]["t"], 2)
        self.assertEqual(f["cross"]["dir"], "上穿")
        self.assertEqual(f["cross"]["last_side"], "高于")

    def test_no_cross(self):
        f = curve_features({"v": [(0, 0.1), (1, 0.2)]}, thr=0.99)[0]
        self.assertIsNone(f["cross"])

    def test_multi_ids_sorted(self):
        f = curve_features({"b": [(0, 1), (1, 2)], "a": [(0, 2), (1, 1)]})
        self.assertEqual([x["id"] for x in f], ["a", "b"])

    def test_format(self):
        s = format_features(curve_features({"v": [(0, 0), (1, 2)]}, thr=1.0), "tempf")
        self.assertIn("tempf", s)
        self.assertIn("上穿", s)


if __name__ == "__main__":
    unittest.main()
