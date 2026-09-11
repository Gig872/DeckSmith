# -*- coding: utf-8 -*-
import unittest
from pathlib import Path

from postprocess import clean as C

FX = Path(__file__).parent / "fixtures" / "sample.o"


class TestClean(unittest.TestCase):
    def setUp(self):
        self.text = FX.read_text(encoding="utf-8")

    def test_clean_text_strips_ctrl(self):
        self.assertEqual(C.clean_text("0Vol.no. x\n abc"), "Vol.no. x\nabc")

    def test_clean_text_collapses_blanks(self):
        self.assertEqual(C.clean_text("a\n\n\n\nb"), "a\n\nb")

    def test_stats(self):
        s = C.stats(self.text)
        self.assertEqual(s["n_edits"], 2)
        self.assertEqual(s["n_volumes"], 2)
        self.assertEqual(s["n_junctions"], 1)
        self.assertEqual(s["n_errors"], 0)

    def test_error_lines(self):
        self.assertEqual(C.error_lines(self.text), [])


class TestExportTool(unittest.TestCase):
    def test_export_series_writes_file(self):
        import registry
        registry.load_plugins("tools")
        self.assertIn("export_series", registry.names())
        self.assertIn("clean_output", registry.names())
        from config import load
        ws = Path(load().workspace)
        ws.mkdir(parents=True, exist_ok=True)
        dst = ws / "_exp_sample.o"
        dst.write_text(FX.read_text(encoding="utf-8"), encoding="utf-8")
        try:
            out = registry.call("export_series", {"o_path": "_exp_sample.o", "var": "tempf"})
            self.assertIn("已导出", out)
            f = ws / "exports" / "_exp_sample_tempf.csv"
            self.assertTrue(f.is_file())
            self.assertIn("time_s", f.read_text(encoding="utf-8-sig"))
        finally:
            dst.unlink(missing_ok=True)
            for p in (ws / "exports").glob("_exp_sample_*"):
                p.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
