# -*- coding: utf-8 -*-
"""硬题 ①-c：完整事故谱 —— 失流+失水叠加事故序列（SBLOCA with pump trip）。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Agent

ask.set_asker(lambda q: "请自行选择合理默认值并继续（压力/温度/功率/破口/时序取常规值）。")

GOAL = (
    "请构建并**真跑通过**一个『**失流 + 失水叠加事故序列**』（典型如小破口失水伴随泵停，"
    "SBLOCA with pump trip）瞬态算例，写入自主学习库：\n"
    "1) 系统：主泵驱动的**加热通道**（定压/定温入口 → 接管 → **泵** → 加热段 pipe+热构件 → 出口边界），"
    "并在通道（或下游）设一个**破口**（触发阀 → 低压安全壳边界，如 0.1 MPa）；\n"
    "2) **事故序列（多事件时序）**：稳态运行 → **t=5 s 主泵停转（失流）** → **t=15 s 破口开启（失水）**；\n"
    "3) 跑瞬态**足够长（≥40 s）**；\n"
    "4) **物理自洽验收（逐条核对并汇报）**：\n"
    "   a. **阶段①失流**：泵停后**流量惰转下降**、加热段温度**上升**（失流特征）；\n"
    "   b. **阶段②失水**：破口开启后**系统压力下降**、出现**闪蒸两相**（voidg 上升）、**系统质量减少**；\n"
    "   c. **时序可辨**：用**时间历程**给出流量/压力/温度/空泡随时间的变化，两个事件(5 s、15 s)的响应清楚可辨；\n"
    "   d. **质量守恒**：损失质量 ≈ 破口累计流出量（误差小）；\n"
    "   e. **能量守恒**：加热功率 ≈ 流体带走 + 蓄热（量级自洽）。\n"
    "5) 做不出来就说明卡点（如多事件时序控制、两相数值稳定性等）。\n"
    "完成后把这份可跑算例存入自主学习库，并用自然语言讲清事故进程的故事。"
)

r = Agent().run(GOAL)
L = []
L.append("SAY: " + (r.say or "(无)")[:2500])
if r.stopped:
    L.append("STOP: " + r.stopped)
L.append("BUDGET: " + " || ".join(r.notes))
L.append("=" * 70)
for i, t in enumerate(r.trace):
    L.append(f"\n----- step {i+1}: {t['tool']} -----")
    L.append("ARGS: " + str(t.get("args"))[:350])
    L.append("RESULT: " + str(t.get("result"))[:700])
open("hard8_out.txt", "w", encoding="utf-8").write("\n".join(L))
