# -*- coding: utf-8 -*-
import unittest

from ui.events import fmt_event


class TestFmtEvent(unittest.TestCase):
    def test_step(self):
        self.assertIn("第 2 步", fmt_event("step", {"step": 2}))

    def test_assistant_has_reasoning_and_content(self):
        s = fmt_event("assistant", {"content": "好的", "reasoning": "先想一下"})
        self.assertIn("【思考】", s)
        self.assertIn("【模型】", s)

    def test_tool_call(self):
        s = fmt_event("tool", {"name": "lookup_doc", "args": {"query": "branch"}})
        self.assertTrue(s.startswith("▶ 调用 lookup_doc"))

    def test_tool_result(self):
        s = fmt_event("tool_result", {"name": "lookup_doc", "result": "…"})
        self.assertTrue(s.startswith("◀ lookup_doc"))

    def test_final_is_marker_only(self):
        # 正文已在 assistant 事件显示，final 只给标记，不重复
        s = fmt_event("final", {"say": "这是正文", "stopped": ""})
        self.assertNotIn("这是正文", s)
        self.assertIn("本轮结束", s)

    def test_stop_marker(self):
        self.assertIn("步数超过上限", fmt_event("final", {"say": "", "stopped": "步数超过上限"}))


if __name__ == "__main__":
    unittest.main()
