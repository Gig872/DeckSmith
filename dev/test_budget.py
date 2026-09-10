# -*- coding: utf-8 -*-
"""验证目标自适应预算：起档分级 + 苛刻升级 + 硬顶封死。"""
from config import Settings
from safety import Guard, classify_goal, GOAL_TIERS

L = []
L.append("===== classify_goal 起档 =====")
cases = [
    ("请用『单一控制体 snglvol』建一个最小可跑的 RELAP5 模型并真跑通过。", "S"),
    ("请建一个含 branch（分支部件）的 RELAP5 最小可跑模型并真跑通过。", "S"),
    ("建一个两控制体 pipe + sngljun 串联的稳态模型。", "M"),
    ("请搭建一个完整的一二回路整体式压水堆瞬态模型，含稳压器、蒸汽发生器、"
     "点堆、停堆、安注、控制系统。", "XL"),
    ("", "M"),
]
ok = True
for text, want in cases:
    got = classify_goal(text)
    flag = "OK " if got == want else "!! "
    if got != want:
        ok = False
    L.append(f"{flag}tier={got} (期望{want})  «{text[:36]}»")

L.append("\n===== 苛刻升级 =====")
s = Settings()   # 默认硬顶：200/5400/12e6/600k
g = Guard(s, goal="建一个最小 snglvol 模型")
L.append(f"起档 tier={g.budget.tier} cur={g.budget.cur}")

n0 = g.maybe_grow(step=21)
L.append(f"① 已接近步数上限但【无进展】→ 放宽结果={n0!r}（应为空串，不许放宽）")

g.observe(30, "parse_output", "正常结束=True  错误数=0")   # 制造真实进展
n1 = g.maybe_grow(step=31)
L.append(f"② 有进展 + 接近上限 → 放宽={n1!r}  cur={g.budget.cur}")

n2 = g.maybe_grow(step=32)   # 冷却期内
L.append(f"③ 冷却期内再调 → {n2!r}（应为空）")

# 空转 → 冻结
g.observe(40, "parse_output", "错误数=0")
g._healthy = False
n3 = g.maybe_grow(step=45)
L.append(f"④ 有空转迹象 → {n3!r}（应为空，冻结）")
g._healthy = True

# 硬顶封死
g.budget.cur["steps"] = 190
g.budget.last_progress_step = 46
g.budget._last_up_step = 0
g.budget.ups = 0
n4 = g.maybe_grow(step=46)
L.append(f"⑤ 逼近硬顶 → {n4!r}  steps={g.budget.cur['steps']}（必须 <= {g.budget.hard['steps']}）")
if g.budget.cur["steps"] > g.budget.hard["steps"]:
    ok = False

# 升级次数上限
g.budget.cur = dict(GOAL_TIERS["S"])
g.budget.ups = 3
g.budget._last_up_step = 0
g.budget.last_progress_step = 100
n5 = g.maybe_grow(step=100)
L.append(f"⑥ 升级次数用尽 → {n5!r}（应为空）")

L.append("\n结论：" + ("全部通过" if ok else "存在不符项，见 !! 行"))
open("budget_test_out.txt", "w", encoding="utf-8").write("\n".join(L))
