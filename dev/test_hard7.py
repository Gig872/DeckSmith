# -*- coding: utf-8 -*-
"""硬题 ②-c：临界流/声速壅塞（choked flow）——扫描背压看质量流量是否达壅塞平台。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Agent

ask.set_asker(lambda q: "请自行选择合理默认值并继续（上游压力/温度/破口面积/背压范围取常规值）。")

GOAL = (
    "请构建并**真跑通过**一个『**临界流 / 声速壅塞（choked flow）**』两相算例，写入自主学习库：\n"
    "1) 模型：**上游高压储液**（固定压力/温度的 tmdpvol，如 8 MPa、560 K 过冷液，或高温高压 snglvol）"
    "→ **破口/喷嘴接管**（给定面积，开启）→ **下游低压边界**（tmdpvol，**背压可调**）；工况稳态；\n"
    "2) **用 `batch_sim` 扫描下游背压**（如 0.1 / 1 / 2 / 3 / 4 / 6 MPa），观察破口**质量流量**；\n"
    "3) **物理自洽验收（逐条核对并汇报）**：\n"
    "   a. **未壅塞区**：背压降低时，破口流量随之**增大**；\n"
    "   b. **壅塞区**：当上下游压比超过**临界压比**后，破口流量**不再随背压下降而增大**"
    "（出现**流量平台**，即声速壅塞）；\n"
    "   c. 由扫描结果**给出临界压比与临界流量的估计**；\n"
    "   d. 破口处应出现**两相/闪蒸**（高速泄放导致）；质量/能量守恒。\n"
    "4) 做不出来就说明卡点（如壅塞模型设置、两相临界流数值问题等）。\n"
    "完成后把可跑算例（及背压扫描模板）存入自主学习库，并用自然语言讲清物理故事。"
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
open("hard7_out.txt", "w", encoding="utf-8").write("\n".join(L))
