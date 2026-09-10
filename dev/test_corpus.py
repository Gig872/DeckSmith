# -*- coding: utf-8 -*-
"""大任务：让 agent 自主规划并构建"覆盖全面"的 RELAP5 参考库（小/中/大参考例）。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Agent

ask.set_asker(lambda q: "请自行规划并选择合理默认值继续（覆盖优先，参数取常规值）。")

GOAL = (
    "请为 RELAP5 智能体**自主规划并构建一套覆盖全面的参考例库**，写入 reference 参考库：\n"
    "1) 分三个规模：**小参考例**（最小/单部件）、**中参考例**（多部件连接）、"
    "**大参考例**（复杂系统，含控制/瞬态/多物理耦合）；\n"
    "2) 尽量**覆盖主流部件类型**（tmdpvol/tmdpjun/snglvol/sngljun/pipe/branch/valve/pump/"
    "heat structure/trip/control 等）与**典型工况**（稳态、瞬态）；\n"
    "3) 每个参考例都必须**真跑通过、物理自洽**（质量/能量守恒），用 "
    "`save_example(..., lib=\"reference\")` 写入参考库；\n"
    "4) **先给出你的覆盖规划清单**（矩阵：规模 × 部件类型 × 工况），再逐个实现、真跑、验证、写入。\n"
    "完成后汇报：覆盖了什么、没覆盖什么、为什么（做不到的说明卡点）。"
)

r = Agent().run(GOAL)
L = []
L.append("SAY: " + (r.say or "(无)"))
if r.stopped:
    L.append("STOP: " + r.stopped)
L.append("BUDGET: " + " || ".join(r.notes))
L.append("=" * 70)
for i, t in enumerate(r.trace):
    L.append(f"\n----- step {i+1}: {t['tool']} -----")
    L.append("ARGS: " + str(t.get("args"))[:400])
    L.append("RESULT: " + str(t.get("result"))[:800])
open("corpus_out.txt", "w", encoding="utf-8").write("\n".join(L))
