# -*- coding: utf-8 -*-
"""逐族 L3 适用性标定：对每族的参考解（已知良好）分别施加「饱和」「能量」判据，
   哪条判据让参考解存疑 → 该族该判据不适用。只跑本地 RELAP5，不烧 token。"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = r"C:\relap-5\agent-kit"
BENCH = os.path.join(ROOT, "bench")
os.environ.setdefault("AGENT_WORKSPACE", os.path.join(ROOT, "workspace_l3cal"))
sys.path.insert(0, ROOT)
sys.path.insert(0, BENCH)
import registry  # noqa: E402
registry.load_plugins("tools")
import tools.relap5 as R  # noqa: E402
from tools.verify import assess  # noqa: E402

OUT = r"C:\relap-5\论文\_l3_matrix.txt"
PER = 3
buf = []
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def P(*a):
    s = " ".join(str(x) for x in a)
    buf.append(s)
    print(s)


tasks = [json.loads(l) for l in open(os.path.join(BENCH, "tasks.jsonl"), encoding="utf-8")]
exp = {r["task_id"]: r for r in (json.loads(l) for l in
       open(os.path.join(BENCH, "expected.jsonl"), encoding="utf-8"))}
picked = {}
for t in tasks:
    if not exp.get(t["task_id"], {}).get("valid"):
        continue
    picked.setdefault(t["family"], [])
    if len(picked[t["family"]]) < PER:
        picked[t["family"]].append(t)

P(f"{'族':22s} {'n':>3s} {'饱和存疑':>8s} {'能量存疑':>8s}   判定")
matrix = {}
for fam, ts_ in sorted(picked.items()):
    ns = ne = n = 0
    for t in ts_:
        rel = f"cal_{t['task_id']}.i"
        R._SB.resolve(rel).write_text(t["reference"], encoding="utf-8")
        msg = R.run_relap5(rel, timeout=900)
        m = re.search(r"输出=(\S+)", msg)
        if not (m and "正常结束=True" in msg):
            continue
        n += 1
        a = assess(m.group(1), power=(t.get("params") or {}).get("power"),
                   mdot=(t.get("params") or {}).get("mdot"))
        if a["n_sat_doubt"]:
            ns += 1
        if a["n_energy_doubt"]:
            ne += 1
    sat_ok = (ns == 0)
    energy_ok = (ne == 0)
    matrix[fam] = {"sat": sat_ok, "energy": energy_ok}
    verdict = []
    if not sat_ok:
        verdict.append("饱和不适用")
    if not energy_ok:
        verdict.append("能量不适用")
    P(f"{fam:22s} {n:3d} {ns:8d} {ne:8d}   {'、'.join(verdict) if verdict else '全部适用 ✓'}")

P("")
P("=" * 70)
P("建议写入 bench/harness.py 的 L3_POLICY（仅列不适用的族）")
P("=" * 70)
P("L3_POLICY = {")
for fam, m in sorted(matrix.items()):
    if not (m["sat"] and m["energy"]):
        P(f'    "{fam}": {{"sat": {m["sat"]}, "energy": {m["energy"]}}},')
P("}")

open(OUT, "w", encoding="utf-8").write("\n".join(buf))
print("->", OUT)
