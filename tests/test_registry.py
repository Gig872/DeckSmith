# -*- coding: utf-8 -*-
import unittest

import registry


class TestRegistry(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        registry.load_plugins("tools")

    def test_core_tools_present(self):
        names = registry.names()
        for t in ("lookup_doc", "run_relap5", "check_sanity", "result_summary",
                  "transient_history", "batch_sim", "ask_user", "save_example"):
            self.assertIn(t, names)

    def test_expected_count(self):
        self.assertGreaterEqual(len(registry.names()), 25)

    def test_schemas_wellformed(self):
        for s in registry.schemas():
            self.assertEqual(s.get("type"), "function")
            fn = s.get("function", {})
            self.assertTrue(fn.get("name"))
            self.assertEqual(fn.get("parameters", {}).get("type"), "object")

    def test_call_unknown_tool(self):
        self.assertIn("未知工具", registry.call("no_such_tool", {}))


if __name__ == "__main__":
    unittest.main()
