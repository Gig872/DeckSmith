# -*- coding: utf-8 -*-
"""验证：自然语言批量仿真的"先协商框架、再问参数范围"完整流程。"""
import registry
registry.load_plugins("tools")
import tools.ask as ask
from core import Session

# 分阶段应答器：先给"框架"，再给"参数范围"（模拟用户逐轮回答）
_stage = {"n": 0}
def asker(q):
    _stage["n"] += 1
    if _stage["n"] == 1:
        return ("基准模型就用水平单管：pipe 4 控制体、流通面积 0.02 m2、总长 1 m、粗糙度 4.5e-5，"
                "两端各接一个 tmdpvol 定压边界；稳态工况就行。")
    return ("扫描入口质量流量，取 5、10、15、20 kg/s 四档；观察出口温度，以及整段的压降。")
ask.set_asker(asker)

L = []
sess = Session()

L.append("========== 第 1 轮（含糊的批量请求） ==========")
r1 = sess.send("我想让你帮我做一批仿真，看看某个参数对结果的影响。")
L.append("SAY: " + (r1.say or "(无)")[:900])
if r1.stopped:
    L.append("STOP: " + r1.stopped)
L.append("TOOLS: " + " | ".join(t["tool"] for t in r1.trace))
L.append("BATCH_PLAN:\n" + sess.batch_text())
L.append("REQS:\n" + sess.requirements_text())

L.append("\n========== 第 2 轮（给范围/确认） ==========")
r2 = sess.send("范围就按你说的来，直接批量跑吧。")
L.append("SAY: " + (r2.say or "(无)")[:1200])
if r2.stopped:
    L.append("STOP: " + r2.stopped)
L.append("TOOLS: " + " | ".join(t["tool"] for t in r2.trace))
L.append("BATCH_PLAN:\n" + sess.batch_text())

# 把 batch_sim 等关键步骤的参数/结果也留档
L.append("\n========== 关键步骤明细 ==========")
for i, t in enumerate(r1.trace + r2.trace):
    if t["tool"] in ("set_batch_plan", "ask_user", "batch_sim", "write_file"):
        L.append(f"{t['tool']}: ARGS={str(t.get('args'))[:300]}")
        L.append(f"   RESULT={str(t.get('result'))[:500]}")

open("batch_agent_out.txt", "w", encoding="utf-8").write("\n".join(L))
