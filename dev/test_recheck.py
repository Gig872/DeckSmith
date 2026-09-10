# -*- coding: utf-8 -*-
"""重跑 branch（看理念改动后是否改善）+ 复核 snglvol（不退化）。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Agent

ask.set_asker(lambda q: "请自行选择合理默认值并继续。")
lines = []

lines.append("========== 重跑 branch ==========")
r1 = Agent().run("请建一个含 branch（分支部件）的 RELAP5 最小可跑模型并真跑通过；"
                 "完成后把这份可跑样例存入自主学习库。")
lines.append("SAY: " + (r1.say or "(无)")[:800])
if r1.stopped:
    lines.append("STOP: " + r1.stopped)
lines.append("TOOLS: " + " | ".join(t["tool"] for t in r1.trace))
lines.append("BUDGET: " + " || ".join(r1.notes))

lines.append("\n========== 复核 snglvol ==========")
r2 = Agent().run("请用『单一控制体 snglvol』建一个最小可跑的 RELAP5 模型并真跑通过。")
lines.append("SAY: " + (r2.say or "(无)")[:600])
if r2.stopped:
    lines.append("STOP: " + r2.stopped)
lines.append("TOOLS: " + " | ".join(t["tool"] for t in r2.trace))
lines.append("BUDGET: " + " || ".join(r2.notes))

open("recheck_out.txt", "w", encoding="utf-8").write("\n".join(lines))
