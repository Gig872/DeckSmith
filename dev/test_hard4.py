# -*- coding: utf-8 -*-
"""硬题 ③：一二次回路耦合（两回路 + 蒸汽发生器换热面耦合）。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Agent

ask.set_asker(lambda q: "请自行选择合理默认值并继续（功率/流量/几何/时长取常规值）。")

GOAL = (
    "请构建并**真跑通过**一个『**一二次回路耦合**』算例，写入自主学习库：\n"
    "1) **一回路**：泵驱动（或定流量边界）的回路，含**加热段**（热构件，模拟堆芯，恒定功率）"
    "与**蒸汽发生器一次侧**（pipe 段）；\n"
    "2) **二回路**：给水（定流量）流经**蒸汽发生器二次侧**（pipe 段），被加热（可沸腾出蒸汽）后排出；\n"
    "3) **耦合**：用一个**热构件**做蒸汽发生器换热面——**左边界接一回路控制体、右边界接二回路控制体**，"
    "热量从一回路经壁面传给二回路；\n"
    "4) 先稳态，再做一个**瞬态**（如一回路功率阶跃 或 二回路给水流量变化），跑足够长；\n"
    "5) **物理自洽验收（逐条核对并汇报）**：\n"
    "   a. **热量确实从一回路传到二回路**（能量守恒：一回路放热 ≈ 二回路吸热）；\n"
    "   b. 一回路温度**沿程下降**、二回路温度**沿程上升**（或二次侧沸腾）；\n"
    "   c. 两侧流量与能量平衡自洽；\n"
    "   d. 质量守恒（误差小）；\n"
    "   e. 瞬态响应合理（如功率阶跃后两侧温度如何变）。\n"
    "6) 做不出来就说明卡在哪（如换热面两侧边界设置、两回路数值耦合不稳定等）。\n"
    "完成后把这份可跑算例存入自主学习库，并用自然语言讲清物理故事（谁放热、谁吸热、能量怎么走）。"
)

r = Agent().run(GOAL)
L = []
L.append("SAY: " + (r.say or "(无)")[:2000])
if r.stopped:
    L.append("STOP: " + r.stopped)
L.append("BUDGET: " + " || ".join(r.notes))
L.append("=" * 70)
for i, t in enumerate(r.trace):
    L.append(f"\n----- step {i+1}: {t['tool']} -----")
    L.append("ARGS: " + str(t.get("args"))[:350])
    L.append("RESULT: " + str(t.get("result"))[:700])
open("hard4_out.txt", "w", encoding="utf-8").write("\n".join(L))
