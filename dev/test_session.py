# -*- coding: utf-8 -*-
"""验证第 4 层：多轮会话跨轮记忆 + 引导澄清 + 水平记录 + 术语/需求工具。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Session

# 模拟一个"新手"用户：含糊需求；被问到时给出可用的具体值
ask.set_asker(lambda q: "我不太懂，你按常规默认来（水平管，面积0.05，长1m，"
                        "入口1MPa/300K，出口0.9MPa，稳态跑10s）就行。")

L = []
sess = Session()

L.append("========== 第 1 轮（含糊需求） ==========")
r1 = sess.send("帮我建个管道模型")
L.append("SAY: " + (r1.say or "(无)")[:900])
if r1.stopped:
    L.append("STOP: " + r1.stopped)
L.append("TOOLS: " + " | ".join(t["tool"] for t in r1.trace))
L.append(f"META: turn={sess.meta['turn']} level={sess.meta['user_level']}")
L.append("REQS:\n" + sess.requirements_text())

L.append("\n========== 第 2 轮（采纳默认） ==========")
r2 = sess.send("参数就用你说的默认吧，直接建并跑通。")
L.append("SAY: " + (r2.say or "(无)")[:900])
if r2.stopped:
    L.append("STOP: " + r2.stopped)
L.append("TOOLS: " + " | ".join(t["tool"] for t in r2.trace))
L.append(f"META: turn={sess.meta['turn']} level={sess.meta['user_level']} artifacts={sess.meta['artifacts']}")
L.append("REQS:\n" + sess.requirements_text())

open("session_test_out.txt", "w", encoding="utf-8").write("\n".join(L))
