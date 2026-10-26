# -*- coding: utf-8 -*-
"""逐族审计 L3 判据的有效性：参考解（已知良好）能否通过？
   参考解自己都过不了的族 → 该族的 L3 判据作废，标"未覆盖"。
   只跑本地 RELAP5，不烧 token。"""
from __future__ import annotations

import json
import os
import re
import sys

ROOT = r"C:\relap-5\agent-kit"
BENCH = os.path.join(ROOT, "bench")
os.environ.setdefault("AGENT_WORKSPACE", os.path.join(ROOT, "workspace_l3audit"))
sys.path.insert(0, ROOT)
sys.path.insert(0, BENCH)
import registry  # noqa: E402
registry.load_plugins("tools")
import tools.relap5 as R  # noqa: E402
from tools.verify import assess  # noqa: E402

OUT = r"C:\relap-5\论文\_l3_family_audit.txt"
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
    fam = t["family"]
    if len(picked.setdefault(fam, [])) < PER:
        picked[fam].append(t)

stat = {}
for fam, ts_ in sorted(picked.items()):
    rows = []
    for t in ts_:
        rel = f"l3a_{t['task_id']}.i"
        R._SB.resolve(rel).write_text(t["reference"], encoding="utf-8")
        msg = R.run_relap5(rel, timeout=900)
        m = re.search(r"输出=(\S+)", msg)
        if not (m and "正常结束=True" in msg):
            rows.append((t["task_id"], None, None, None))
            continue
        a = assess(m.group(1), power=(t.get("params") or {}).get("power"),
                   mdot=(t.get("params") or {}).get("mdot"))
        rows.append((t["task_id"], a["n_pass"], a["n_doubt"], a["sat_max_margin"]))
    stat[fam] = rows
    bad = sum(1 for _, _, nd, _ in rows if nd)
    P(f"{fam:22s} n={len(rows)}  参考解存疑题数={bad}  " +
      " | ".join(f"{tid.split('_')[-1]}:doubt={nd},sat={sm}" for tid, _, nd, sm in rows))

P("")
P("=" * 70)
P("结论：以下族的参考解自身即存疑 → 该族 L3 判据作废（标未覆盖）")
P("=" * 70)
for fam, rows in sorted(stat.items()):
    bad = [tid for tid, _, nd, _ in rows if nd]
    if bad:
        P(f"  {fam:22s} 存疑 {len(bad)}/{len(rows)}  {bad}")

open(OUT, "w", encoding="utf-8").write("\n".join(buf))
print("->", OUT)
