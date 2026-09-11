# -*- coding: utf-8 -*-
import unittest
from pathlib import Path

from tools.verify import verify_result

_HDR = ("time= 0.0\n"
        "  Vol.no.  pressure      voidf        voidg        voidgo        tempf      tempg\n")


def _o(rows):
    """rows: list of (id, p, voidf, voidg, voidgo, tempf, tempg)。"""
    body = "".join(f"  {r[0]}  {r[1]}  {r[2]}  {r[3]}  {r[4]}  {r[5]}  {r[6]}\n" for r in rows)
    return _HDR + body


class TestVerify(unittest.TestCase):
    def setUp(self):
        self.f = Path("workspace") / "_verify_test.o"
        self.f.parent.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        try:
            self.f.unlink()
        except OSError:
            pass

    def _run(self, text, **kw):
        self.f.write_text(text, encoding="utf-8")
        return verify_result(o_path="_verify_test.o", **kw)

    def test_subcooled_liquid_passes(self):
        r = self._run(_o([("110-010000", "1.00000E+06", 1.0, 0.0, 0.0, 300.0, 453.0)]))
        self.assertIn("通过 1", r)
        self.assertIn("存疑 0", r)

    def test_two_phase_consistent_passes(self):
        r = self._run(_o([("110-010000", "1.00000E+06", 0.5, 0.5, 0.5, 453.03, 453.03)]))
        self.assertIn("存疑 0", r)

    def test_two_phase_inconsistent_flags(self):
        r = self._run(_o([("110-010000", "1.00000E+06", 0.5, 0.5, 0.5, 350.0, 350.0)]))
        self.assertIn("存疑 1", r)
        self.assertIn("两相", r)

    def test_superheated_liquid_flags(self):
        r = self._run(_o([("110-010000", "1.00000E+06", 1.0, 0.0, 0.0, 500.0, 500.0)]))
        self.assertIn("存疑 1", r)
        self.assertIn("过热", r)

    def test_superheated_vapor_passes(self):
        r = self._run(_o([("110-010000", "1.00000E+06", 0.0, 1.0, 0.0, 500.0, 500.0)]))
        self.assertIn("存疑 0", r)

    def test_energy_balance_ok(self):
        # Q=1e6 W, mdot=10, tin=300 → ΔT≈23.9K
        r = self._run(_o([("110-010000", "1.00000E+06", 1.0, 0.0, 0.0, 323.9, 453.0)]),
                      power=1_000_000, mdot=10.0, tin=300.0)
        self.assertIn("能量平衡", r)
        self.assertIn("同量级", r)

    def test_energy_balance_bad(self):
        r = self._run(_o([("110-010000", "1.00000E+06", 1.0, 0.0, 0.0, 450.0, 453.0)]),
                      power=1_000_000, mdot=10.0, tin=300.0)
        self.assertIn("存疑", r)

    def test_missing_file(self):
        self.assertIn("不存在", verify_result(o_path="_no_such.o"))


if __name__ == "__main__":
    unittest.main()
