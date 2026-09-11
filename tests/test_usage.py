# -*- coding: utf-8 -*-
import unittest

from usage import Usage, price_of


class TestUsage(unittest.TestCase):
    def test_price_known_and_unknown(self):
        self.assertEqual(price_of("gpt-4o-mini")[2], "USD")
        self.assertEqual(price_of("deepseek-chat")[2], "CNY")
        self.assertEqual(price_of("no-such-model-xyz")[2], "?")

    def test_price_prefix_match(self):
        # 前缀匹配（如 deepseek-v4-flash-xxx 命中 deepseek-v4-flash）
        self.assertNotEqual(price_of("deepseek-v4-flash-latest")[2], "?")

    def test_accumulate(self):
        u = Usage()
        u.add({"prompt_tokens": 1000, "completion_tokens": 500}, "deepseek-chat")
        u.add({"prompt_tokens": 2000, "completion_tokens": 1000}, "deepseek-chat")
        self.assertEqual(u.calls, 2)
        self.assertEqual(u.tokens_in, 3000)
        self.assertEqual(u.tokens_out, 1500)
        self.assertGreater(u.cost, 0)
        self.assertEqual(u.by_model["deepseek-chat"][0], 2)

    def test_roundtrip(self):
        u = Usage()
        u.add({"prompt_tokens": 10, "completion_tokens": 20}, "deepseek-chat")
        v = Usage()
        v.load(u.to_dict())
        self.assertEqual((v.calls, v.tokens_in, v.tokens_out), (1, 10, 20))

    def test_reset(self):
        u = Usage()
        u.add({"prompt_tokens": 5, "completion_tokens": 5}, "deepseek-chat")
        u.reset()
        self.assertEqual((u.calls, u.tokens_in, u.tokens_out, u.cost), (0, 0, 0, 0.0))


if __name__ == "__main__":
    unittest.main()
