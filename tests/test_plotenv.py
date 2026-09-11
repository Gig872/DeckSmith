# -*- coding: utf-8 -*-
import sys
import tempfile
import unittest
from pathlib import Path

import plotenv
from postprocess.plot import chart_spec, render_png, matplotlib_available

_HAS_MPL = matplotlib_available()


class TestPlotEnv(unittest.TestCase):
    def test_available_is_bool(self):
        self.assertIsInstance(plotenv.available(), bool)

    def test_can_install_tuple(self):
        ok, why = plotenv.can_install()
        self.assertIsInstance(ok, bool)
        self.assertIsInstance(why, str)

    def test_frozen_cannot_install(self):
        old = getattr(sys, "frozen", None)
        sys.frozen = True
        try:
            self.assertTrue(plotenv.is_frozen())
            ok, why = plotenv.can_install()
            self.assertFalse(ok)
            self.assertIn("打包版", why)
        finally:
            if old is None:
                delattr(sys, "frozen")
            else:
                sys.frozen = old

    @unittest.skipUnless(_HAS_MPL, "未装 matplotlib")
    def test_ensure_no_confirm_needed_when_available(self):
        called = []

        def confirm(_msg):
            called.append(1)
            return False          # 已可用时不应征询

        ok, _msg = plotenv.ensure(confirm)
        self.assertTrue(ok)
        self.assertEqual(called, [])

    @unittest.skipUnless(_HAS_MPL, "未装 matplotlib")
    def test_install_noop_when_available(self):
        ok, msg = plotenv.install()
        self.assertTrue(ok)
        self.assertIn("已可用", msg)

    @unittest.skipUnless(_HAS_MPL, "未装 matplotlib")
    def test_render_png(self):
        d = tempfile.mkdtemp(prefix="plot_")
        dst = Path(d) / "out.png"
        p = render_png({"a": [(0, 1), (1, 3)]}, dst, title="t", ylabel="y")
        self.assertTrue(p and Path(p).is_file())

    def test_chart_spec_still_pure(self):
        # 确认绘图数据层不依赖 matplotlib
        spec = chart_spec({"a": [(0, 1), (1, 2)]})
        self.assertEqual(len(spec["lines"]), 1)


if __name__ == "__main__":
    unittest.main()
