# -*- coding: utf-8 -*-
import math
import unittest

from postprocess import water as W


class TestWater(unittest.TestCase):
    def test_sat_temp_atm(self):
        self.assertAlmostEqual(W.sat_temp_K(101325.0), 373.15, delta=0.2)

    def test_sat_temp_1mpa(self):
        self.assertAlmostEqual(W.sat_temp_K(1.0e6), 453.03, delta=0.6)

    def test_sat_temp_10mpa(self):
        self.assertAlmostEqual(W.sat_temp_K(10.0e6), 584.15, delta=0.8)

    def test_sat_temp_out_of_range(self):
        self.assertTrue(math.isnan(W.sat_temp_K(30.0e6)))   # 超临界压力
        self.assertTrue(math.isnan(W.sat_temp_K(0.0)))
        self.assertTrue(math.isnan(W.sat_temp_K(-5)))

    def test_sat_temp_monotonic(self):
        ts = [W.sat_temp_K(p) for p in (1e5, 1e6, 5e6, 10e6)]
        self.assertEqual(ts, sorted(ts))

    def test_cp_liquid(self):
        self.assertTrue(4.0 < W.cp_liquid(293.15) < 4.4)    # 20℃ ≈ 4.18
        self.assertTrue(4.0 < W.cp_liquid(473.15) < 4.7)    # 200℃
        self.assertTrue(W.cp_liquid(700.0) > 4.0)           # 超范围取端点

    def test_h_fg(self):
        self.assertAlmostEqual(W.h_fg(101325.0), 2256.4, delta=60)
        self.assertGreater(W.h_fg(1e6), W.h_fg(10e6))       # 压力↑潜热↓


if __name__ == "__main__":
    unittest.main()
