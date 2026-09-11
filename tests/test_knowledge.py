# -*- coding: utf-8 -*-
import os
import tempfile
import unittest

import registry
registry.load_plugins("tools")
import tools.knowledge as K


class TestKnowledgeHelpers(unittest.TestCase):
    def test_terms_tokenize(self):
        t = K._terms("branch component cards")
        self.assertIn("branch", t)          # 分词后能命中部件名（整句不再当一个词）
        self.assertNotIn("cards", t)        # 噪声词被过滤

    def test_family(self):
        self.assertEqual(K._family("A-7.7.4 CCC0201 卡"), "7.7")

    def test_num_prefix(self):
        self.assertEqual(K._num_prefix("A-8 1CCCGXNN 热构件的输入"), "8")
        self.assertEqual(K._num_prefix("A-8.13 卡"), "8.13")
        self.assertEqual(K._num_prefix("A-7.6 管型部件"), "7.6")

    def test_glossary(self):
        r = K.glossary("水力直径")
        self.assertIn("水力直径", r)

    def test_lookup_with_temp_doc(self):
        d = tempfile.mkdtemp(prefix="deck_")
        p = os.path.join(d, "manual.md")
        with open(p, "w", encoding="utf-8") as f:
            f.write("# A-7.7 分支、分离器部件\n一句话说明。\n"
                    "### A-7.7.1 信息卡\n- **W1** 接管数 NJ。\n"
                    "#### A-7.7.2 几何卡\n- **W1** 流通面积。\n")
        old = os.environ.get("RELAP5_DOC")
        os.environ["RELAP5_DOC"] = p
        try:
            registry.reset_counts()
            r = K.lookup_doc("branch")
            self.assertIn("A-7.7", r)        # 家族检索：整组小节一起返回
            self.assertIn("A-7.7.1", r)
        finally:
            if old is None:
                os.environ.pop("RELAP5_DOC", None)
            else:
                os.environ["RELAP5_DOC"] = old


if __name__ == "__main__":
    unittest.main()
