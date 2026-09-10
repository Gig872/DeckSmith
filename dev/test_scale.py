# -*- coding: utf-8 -*-
"""大规模验证：多部件系统（并联→合流），压"跨部件连接一致性 + 多入口分支"。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Agent

ask.set_asker(lambda q: "请自行选择合理默认值并继续，几何/边界沿用参考样例的常规取值。")

GOAL = ("请搭建一个『两通道并联再合流』的 RELAP5 稳态系统并真跑通过："
        "入口 tmdpvol → sngljun → 分支部件 branch(一进两出) → 两条并联管道 pipe → "
        "合流分支部件 branch(两进一出) → sngljun → 出口 tmdpvol；"
        "完成后把这份可跑样例存入自主学习库。")

r = Agent().run(GOAL)
L = []
L.append("SAY: " + (r.say or "(无)"))
if r.stopped:
    L.append("STOP: " + r.stopped)
L.append("BUDGET: " + " || ".join(r.notes))
L.append("=" * 70)
for i, t in enumerate(r.trace):
    L.append(f"\n----- step {i+1}: {t['tool']} -----")
    L.append("ARGS: " + str(t.get("args"))[:500])
    L.append("RESULT: " + str(t.get("result"))[:1200])
open("scale_test_out.txt", "w", encoding="utf-8").write("\n".join(L))
