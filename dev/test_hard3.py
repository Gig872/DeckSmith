# -*- coding: utf-8 -*-
"""硬题 ①-b：失水事故(LOCA)瞬态 —— 破口泄压 → 闪蒸两相 → 压力/温度/存量变化。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Agent

ask.set_asker(lambda q: "请自行选择合理默认值并继续（初始压力/温度/破口面积/时长取常规值）。")

GOAL = (
    "请构建并**真跑通过**一个『**失水事故（LOCA, loss of coolant / 小破口泄压）**』瞬态算例，"
    "写入自主学习库：\n"
    "1) 模型：一个**承压高温系统**（用 snglvol / pipe 组成，初始如 15 MPa、600 K 过冷水）"
    "→ 经一个**破口**（阀门 valve 或接管，t=5 s 由 trip 触发打开）→ **低压泄放边界**"
    "（如 tmdpvol 0.1 MPa，模拟安全壳/大气）；\n"
    "2) 瞬态：t=5 s 破口开启，系统**泄压**；\n"
    "3) 跑瞬态**足够长（≥20 s）**；\n"
    "4) **物理自洽验收（必须逐条核对并汇报）**：\n"
    "   a. 系统**压力随时间下降**（给出几个时刻的压力）；\n"
    "   b. **空泡份额上升**（压力跌破饱和后发生**闪蒸/两相**，给出 voidg 随时间）；\n"
    "   c. **温度下降**并**跟随饱和温度**（降压饱和）；\n"
    "   d. **系统质量减少**（工质从破口流出）；\n"
    "   e. **破口流量先大后小**；\n"
    "   f. **质量守恒**（损失的质量 = 破口累计流出量，误差小）。\n"
    "5) 做不出来就说明卡在哪（如两相数值不稳定、物性调用失败等）。\n"
    "完成后把这份可跑算例存入自主学习库，并用自然语言讲清物理故事。"
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
open("hard3_out.txt", "w", encoding="utf-8").write("\n".join(L))
