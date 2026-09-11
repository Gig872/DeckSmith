# -*- coding: utf-8 -*-
import unittest
from pathlib import Path

from postprocess import parse as P
from postprocess import extract as E

FX = Path(__file__).parent / "fixtures" / "sample.o"


class TestParseExtract(unittest.TestCase):
    def setUp(self):
        self.text = FX.read_text(encoding="utf-8")

    def test_series_tempf(self):
        s = E.get_series(self.text, "tempf", ["110-010000"])
        self.assertEqual(s["110-010000"], [(0.0, 300.0), (2.0, 350.0)])

    def test_series_pressure(self):
        s = E.get_series(self.text, "pressure", ["110-010000"])
        self.assertEqual([v for _t, v in s["110-010000"]], [1e6, 9e5])

    def test_series_voidg(self):
        s = E.get_series(self.text, "voidg", ["110-010000"])
        self.assertEqual([v for _t, v in s["110-010000"]], [0.0, 0.5])

    def test_series_mass_flow(self):
        s = E.get_series(self.text, "mass_flow")
        self.assertEqual([v for _t, v in s["102-000000"]], [1.0, 8.0])

    def test_catalog(self):
        c = E.catalog(self.text)
        self.assertEqual(c["times"], [0.0, 2.0])
        self.assertIn("tempf", c["volume_vars"])
        self.assertIn("mass_flow", c["junction_vars"])
        self.assertIn("110-010000", c["volume_ids"])
        self.assertIn("102-000000", c["junction_ids"])

    def test_unknown_var(self):
        self.assertEqual(E.get_series(self.text, "no_such_var"), {})

    def test_clean_ctrl(self):
        self.assertEqual(P.clean_ctrl("0Vol.no. x\n abc"), "Vol.no. x\nabc")


class TestPostprocTools(unittest.TestCase):
    def test_tools_wired_and_run(self):
        import registry
        registry.load_plugins("tools")
        self.assertIn("list_output_vars", registry.names())
        self.assertIn("extract_series", registry.names())
        from config import load
        ws = Path(load().workspace)
        ws.mkdir(parents=True, exist_ok=True)
        dst = ws / "_fixture_sample.o"
        dst.write_text(FX.read_text(encoding="utf-8"), encoding="utf-8")
        try:
            out = registry.call("list_output_vars", {"o_path": "_fixture_sample.o"})
            self.assertIn("tempf", out)
            out2 = registry.call("extract_series",
                                 {"o_path": "_fixture_sample.o", "var": "tempf", "ids": ["110-010000"]})
            self.assertIn("110-010000", out2)
        finally:
            dst.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
