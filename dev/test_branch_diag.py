# -*- coding: utf-8 -*-
"""诊断 branch：把每步工具参数与结果全部落盘，定位卡点。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Agent

ask.set_asker(lambda q: "请自行选择合理默认值并继续。")
r = Agent().run("请建一个含 branch（分支部件）的 RELAP5 最小可跑模型并真跑通过；"
                "完成后把这份可跑样例存入自主学习库。")

lines = []
lines.append("SAY: " + (r.say or "(无)"))
if r.stopped:
    lines.append("STOP: " + r.stopped)
lines.append("=" * 70)
for i, t in enumerate(r.trace):
    lines.append(f"\n----- step {i+1}: {t['tool']} -----")
    lines.append("ARGS: " + str(t.get("args"))[:600])
    lines.append("RESULT: " + str(t.get("result"))[:1500])

open("branch_diag.txt", "w", encoding="utf-8").write("\n".join(lines))
