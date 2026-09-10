# -*- coding: utf-8 -*-
"""硬题 ②-b：临界热流/烧干（CHF/dryout）——用批量功率扫描找烧干起始点。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Agent

ask.set_asker(lambda q: "请自行选择合理默认值并继续（压力/流量/几何/扫描范围取常规值）。")

GOAL = (
    "请构建并**真跑通过**一个『**临界热流 / 烧干（CHF / dryout）**』两相算例，写入自主学习库：\n"
    "1) 模型：入口 tmdpjun 定流量**过冷液**（如 1 kg/s、5 MPa、500 K）→ **竖直受热 pipe**"
    "（≥6 控制体，外侧耦合热构件）→ 出口定压边界；稳态；\n"
    "2) **用 `batch_sim` 做功率扫描**（参数化模板，扫描热构件总功率，从小到大多档，"
    "例如 0.3 / 0.6 / 0.9 / 1.2 / 1.5 MW），自动跑一批工况；\n"
    "3) **物理自洽验收（逐条核对并汇报）**：\n"
    "   a. **小功率**：通道内两相但不烧干（出口 void<1、含汽率<1、壁温平稳）；\n"
    "   b. **大功率**：出现**烧干（dryout / CHF）**——末段 void→1、含汽率→1，"
    "**壁面温度急剧上升**（失去液冷）；\n"
    "   c. 从扫描结果中**给出烧干起始的功率与位置**（哪一段开始干涸）；\n"
    "   d. 各工况**能量守恒**（Q ≈ ṁ·Δh，在烧干前）；\n"
    "   e. **批量汇总**：给出功率 × 出口含汽率/void/壁温 的表（哪些工况正常、哪些烧干/失败）。\n"
    "4) 做不出来就说明卡点（如烧干导致材料导热表越界、数值不收敛等）。\n"
    "完成后把这份可跑算例（及功率扫描模板）存入自主学习库，并用自然语言讲清物理故事。"
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
open("hard6_out.txt", "w", encoding="utf-8").write("\n".join(L))
