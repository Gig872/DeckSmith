# -*- coding: utf-8 -*-
"""硬题 ①-a：失流事故(LOF)瞬态场景 —— 泵停/失流 → 流量惰转 → 加热段升温。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Agent

ask.set_asker(lambda q: "请自行选择合理默认值并继续（功率/几何/时长取常规值）。")

GOAL = (
    "请构建并**真跑通过**一个『**失流事故（LOF, loss of flow）**』瞬态算例，写入自主学习库：\n"
    "1) 模型：一个**主泵驱动**的加热通道 —— 入口定压/定温边界 → 接管 → **泵** → 加热段 "
    "pipe（外侧耦合热构件，恒定功率，模拟堆芯发热）→ 接管 → 出口定压边界；先达到稳态；\n"
    "2) 瞬态：在 **t=5 s 触发『失流』**（主泵停转 / 流量丧失，用 trip + 控制实现），"
    "观察**流量惰转下降**与**加热段温度上升**的响应；\n"
    "3) 跑瞬态**足够长（≥30 s）**；\n"
    "4) **物理自洽验收（必须逐条核对并汇报）**：\n"
    "   a. 流量确实**随时间下降**（惰转/衰减曲线，给出几个时刻的流量值）；\n"
    "   b. 加热段**温升随流量下降而增大**，且大致符合 ΔT≈Q/(ṁ·cp)；\n"
    "   c. 质量守恒（进=出，质量误差小）；\n"
    "   d. **若流量趋于零，温度应持续上升**（不得出现『流量没了、温度却不变』的假结果）。\n"
    "5) 做不出来就说明卡在哪、缺什么信息。\n"
    "完成后把这份可跑算例存入自主学习库（save_example，learned），并用自然语言讲清物理故事。"
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
open("hard2_out.txt", "w", encoding="utf-8").write("\n".join(L))
