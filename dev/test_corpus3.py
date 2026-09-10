# -*- coding: utf-8 -*-
"""聚焦补齐：只做参考库仍缺的部件/特性，做到全覆盖。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Agent

ask.set_asker(lambda q: "请按常规默认值自行决策并继续，目标是补齐覆盖。")

GOAL = (
    "参考库现在仍**缺**以下部件/特性（其余已覆盖），请**只集中补齐这些**，"
    "每个都真跑通过、物理自洽，用 save_example(lib=\"reference\") 写入参考库：\n"
    "1) **mtpljun**（多接管部件）；\n"
    "2) **accum**（安注箱/蓄压箱）；\n"
    "3) **turbine**（透平，含所需的透平性能/特性卡）；\n"
    "4) **pump 自定义相似曲线**（不要只用内置曲线，给出正/反向或多点的自定义曲线）；\n"
    "5) **热构件高级模型**：至少覆盖一种（如间隙传导 gap conduction 或 再淹没 reflood）；\n"
    "6) **反应堆点堆动力学**（point kinetics，功率由堆动力学给出）。\n"
    "每个先 `lookup_doc` 读手册对应章节，再构建、真跑、校验、写入；"
    "**做不出来的必须说明卡在哪、缺手册里的哪条信息**。最后给对账表（这 6 项 ✓/✗）。"
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
open("corpus3_out.txt", "w", encoding="utf-8").write("\n".join(L))
