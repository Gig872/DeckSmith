# -*- coding: utf-8 -*-
import unittest

import registry
from config import Settings
from core import Agent


class TestCoreEvents(unittest.TestCase):
    def setUp(self):
        registry.load_plugins("tools")

    def test_dry_run_emits_events(self):
        s = Settings()
        s.dry_run = True
        kinds = []
        a = Agent(s)
        a.event_cb = lambda k, d: kinds.append(k)
        a.run("随便测试一下")
        for k in ("step", "assistant", "tool", "tool_result", "final"):
            self.assertIn(k, kinds)

    def test_cancel_mid_run(self):
        s = Settings()
        s.dry_run = True
        a = Agent(s)

        def fake(messages, tools=None):
            a.cancel()   # 模拟"运行中途按停止"
            return {"content": "", "tool_calls": [
                {"id": "1", "function": {"name": "get_time", "arguments": "{}"}}]}
        a.llm.complete = fake
        out = a.run("x")
        self.assertEqual(out.stopped, "用户中断")


if __name__ == "__main__":
    unittest.main()
