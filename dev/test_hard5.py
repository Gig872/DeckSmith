# -*- coding: utf-8 -*-
"""硬题 ②：两相专题 —— 受热通道沸腾（含汽率/空泡沿程分布 + 能量守恒）。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Agent

ask.set_asker(lambda q: "请自行选择合理默认值并继续（压力/流量/功率/几何取常规值）。")

GOAL = (
    "请构建并**真跑通过**一个『**受热通道沸腾（含汽率分布）**』两相算例，写入自主学习库：\n"
    "1) 模型：入口 tmdpjun 给定**过冷液**流量（如 1 kg/s、5 MPa、500 K，低于 5 MPa 饱和温度）→ "
    "**受热 pipe**（≥6 控制体，外侧耦合热构件，功率足够把流体加热到**沸腾并产生蒸汽**）→ "
    "出口定压边界；工况**稳态**；\n"
    "2) **物理自洽验收（逐条核对并汇报）**：\n"
    "   a. 沿程出现**过冷 → 沸腾**的过渡：**含汽率 x 沿程递增**（从负值→0→正值）；\n"
    "   b. **空泡份额 void 沿程上升**（单相液 → 两相 → 高含汽）；\n"
    "   c. **两相区温度 ≈ 饱和温度**（等温段）；\n"
    "   d. **能量守恒**：总功率 Q ≈ ṁ·(h_out − h_in)；\n"
    "   e. **质量守恒**（误差小）。\n"
    "3) 做不出来就说明卡点（如两相数值不稳定、含汽率越界等）。\n"
    "完成后把这份可跑算例存入自主学习库，并用自然语言讲清物理故事（热量怎么把过冷液变成两相/蒸汽）。"
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
open("hard5_out.txt", "w", encoding="utf-8").write("\n".join(L))
