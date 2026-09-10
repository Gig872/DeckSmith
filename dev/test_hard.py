# -*- coding: utf-8 -*-
"""大难度流程测试 1：含热构件(heat structure)的加热通道 + 能量守恒验收。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Agent

ask.set_asker(lambda q: "请自行选择合理默认值并继续：几何/热物性沿用常规取值，"
                        "加热功率取约 100 kW，工质液态水。")

GOAL = ("请搭建一个『单通道加热回路』的 RELAP5 稳态模型并真跑通过："
        "入口 tmdpvol（定质量流量 5 kg/s、300 K）→ sngljun → 加热段 pipe（4 控制体，水平，面积 0.01 m2，"
        "长 1 m）→ sngljun → 出口 tmdpvol（定压 1.0 MPa）；加热段外侧耦合一个热构件(heat structure)，"
        "恒定功率加热（总功率约 100 kW）。"
        "要求：跑通后出口温升与 Q/(m·cp) 量级一致（能量守恒），并把可跑样例存入自主学习库。")

r = Agent().run(GOAL)
L = []
L.append("SAY: " + (r.say or "(无)"))
if r.stopped:
    L.append("STOP: " + r.stopped)
L.append("BUDGET: " + " || ".join(r.notes))
L.append("=" * 70)
for i, t in enumerate(r.trace):
    L.append(f"\n----- step {i+1}: {t['tool']} -----")
    L.append("ARGS: " + str(t.get("args"))[:500])
    L.append("RESULT: " + str(t.get("result"))[:1200])
open("hard_test_out.txt", "w", encoding="utf-8").write("\n".join(L))
