# -*- coding: utf-8 -*-
"""最后一项：补齐点堆动力学，并给最终全覆盖对账表。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Agent

ask.set_asker(lambda q: "请按常规默认值自行决策并继续。")

GOAL = (
    "参考库现在**只差一项**：**反应堆点堆动力学（point kinetics）**。\n"
    "请覆盖它：手册对应章节是 **A-12（30000000 卡族，堆动力学）**，另见 A-4.6（反应堆动力学量）。\n"
    "做法：\n"
    "1) `lookup_doc` 读 A-12 全族，理解点堆动力学卡（堆型/信息卡/缓发中子/反应性/衰变热等）；\n"
    "2) 构建一个**含点堆动力学**的模型：功率由点堆动力学给出（可配合热构件把功率传给流体，"
    "或一个加热通道），真跑通过、物理自洽；\n"
    "3) 用 `save_example(..., lib=\"reference\")` 写入参考库；\n"
    "4) 最后给出**最终全覆盖对账表**：本手册全部部件类型（pipe/annulus/snglvol/sngljun/tmdpvol/"
    "tmdpjun/branch/valve/pump/mtpljun/accum/separatr/jetmixer/turbine/eccmix）+ 热构件/阀子类型/"
    "trip/control/通用表/点堆动力学，逐项 ✓/✗，**确认无遗漏**。"
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
open("corpus4_out.txt", "w", encoding="utf-8").write("\n".join(L))
