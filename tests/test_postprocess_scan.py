# -*- coding: utf-8 -*-
import csv
import tempfile
import unittest
from pathlib import Path

from postprocess.scan import scan_series, param_columns, read_summary

FIX = Path(__file__).parent / "fixtures"
FX = FIX / "sample.o"
FX2 = FIX / "sample2.o"


def _write_csv(rows):
    d = tempfile.mkdtemp(prefix="scan_")
    p = Path(d) / "s.csv"
    with open(p, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=["power", "o", "正常结束", "voidg_max"])
        w.writeheader()
        for r in rows:
            w.writerow(r)
    return p


class TestScan(unittest.TestCase):
    def test_param_columns(self):
        p = _write_csv([{"power": 1e6, "o": str(FX), "正常结束": True},
                        {"power": 2e6, "o": str(FX2), "正常结束": True}])
        self.assertEqual(param_columns(p), ["power"])

    def test_read_summary(self):
        p = _write_csv([{"power": 1e6, "o": str(FX), "正常结束": True}])
        cols, rows = read_summary(p)
        self.assertIn("o", cols)
        self.assertEqual(len(rows), 1)

    def test_scan_series_trend(self):
        p = _write_csv([{"power": 1e6, "o": str(FX), "正常结束": True},
                        {"power": 2e6, "o": str(FX2), "正常结束": True}])
        ser = scan_series(p, "power", "tempf", ["110-010000"])
        self.assertEqual([x for x, _y in ser["110-010000"]], [1e6, 2e6])
        self.assertEqual([y for _x, y in ser["110-010000"]], [350.0, 400.0])

    def test_scan_series_max_agg(self):
        p = _write_csv([{"power": 1e6, "o": str(FX), "正常结束": True}])
        ser = scan_series(p, "power", "tempf", ["110-010000"], agg="max")
        self.assertEqual(ser["110-010000"][0][1], 350.0)   # 该 .o 里 tempf 最大 350

    def test_scan_series_missing_o(self):
        p = _write_csv([{"power": 1e6, "o": "no_such.o", "正常结束": False}])
        self.assertEqual(scan_series(p, "power", "tempf"), {})


if __name__ == "__main__":
    unittest.main()
