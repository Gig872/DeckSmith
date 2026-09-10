# -*- coding: utf-8 -*-
"""补齐参考库：要求对 RELAP5 全部部件类型与主要子系统做到**无遗漏覆盖**。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Agent

ask.set_asker(lambda q: "请按常规默认值自行决策并继续，目标是补齐覆盖、不留遗漏。")

GOAL = (
    "参考库已经有小/中/大的一批例，但**还有未覆盖的部件类型**。现在要求：\n"
    "**做到对 RELAP5 部件类型的全覆盖，不得有遗漏。**\n\n"
    "以本手册（relap5输入卡介绍.md）收录为准，需覆盖的**水力学部件类型**全清单：\n"
    "pipe, annulus, snglvol, sngljun, tmdpvol, tmdpjun, branch, valve, pump, mtpljun, "
    "accum, separatr, jetmixer, turbine, eccmix。\n"
    "另有子系统/特性：**热构件及其高级模型、trip、control、通用表(202)、反应堆点堆动力学**。\n"
    "（注：multid/prizer/fwhtr/cprssr 本手册未收录，不在范围内。）\n\n"
    "做法：\n"
    "1) 先 `list_examples` 盘点参考库现状，对照上面全清单**列出手册里有、但参考库还没覆盖的缺口**；\n"
    "2) **逐一补齐所有缺口**：每个都真跑通过、物理自洽，用 `save_example(..., lib=\"reference\")` "
    "写入参考库；\n"
    "3) valve 要覆盖多个子类型（chkvlv 止回 / mtrvlv 马达 / srvvlv 伺服 / relfvlv 释放 等）；\n"
    "4) 难度大的（turbine / eccmix / jetmixer / separatr / mtpljun / accum / annulus / 点堆）"
    "也要做，**做不出来就说明卡在哪、缺哪个手册没写的信息**；\n"
    "5) 最后给出**对账表**：全清单 × 覆盖状态（✓/✗），目标是**无一遗漏**。"
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
    L.append("ARGS: " + str(t.get("args"))[:350])
    L.append("RESULT: " + str(t.get("result"))[:700])
open("corpus2_out.txt", "w", encoding="utf-8").write("\n".join(L))
