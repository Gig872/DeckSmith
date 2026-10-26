# -*- coding: utf-8 -*-
"""从逐体 .o 标定 L2（收敛）与 L3a（饱和一致性）阈值。
   重跑参考解，只花本地算力，不烧 token。"""
from __future__ import annotations

import json
import os
import re
import statistics as st
import sys

ROOT = r"C:\relap-5\agent-kit"
BENCH = os.path.join(ROOT, "bench")
os.environ.setdefault("AGENT_WORKSPACE", os.path.join(ROOT, "workspace_calib"))
sys.path.insert(0, ROOT)
sys.path.insert(0, BENCH)

import registry  # noqa: E402
registry.load_plugins("tools")
import tools.relap5 as R  # noqa: E402
from postprocess.extract import get_series  # noqa: E402
from postprocess.water import sat_temp_K  # noqa: E402

OUT = r"C:\relap-5\论文\_calib_l2l3a.txt"
buf = []
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

STEADY = {"single_pipe_steady", "hs_gap", "chf_dryout", "point_kinetics", "parallel_channels",
          "pump_loop", "turbine", "separator", "mtpljun", "jetmixer", "critical_nozzle",
          "numerical_grid"}


def P(*a):
    s = " ".join(str(x) for x in a)
    buf.append(s)
    print(s)


def last(ser, cid):
    pts = ser.get(cid)
    return pts[-1][1] if pts else None


tasks = [json.loads(l) for l in open(os.path.join(BENCH, "tasks.jsonl"), encoding="utf-8")]
ex = {r["task_id"]: r for r in (json.loads(l) for l in
      open(os.path.join(BENCH, "expected.jsonl"), encoding="utf-8"))}

# 每族最多取 PER 题，且参考解需有效
PER = 4
picked = {}
for t in tasks:
    if not ex.get(t["task_id"], {}).get("valid"):
        continue
    fam = t["family"]
    if fam not in STEADY:
        continue
    if len(picked.setdefault(fam, [])) < PER:
        picked[fam].append(t)

drifts, sats = [], []
P("重跑参考解（本地，不烧 token）……")
for fam, ts_ in sorted(picked.items()):
    for t in ts_:
        rel = f"cal_{t['task_id']}.i"
        R._SB.resolve(rel).write_text(t["reference"], encoding="utf-8")
        msg = R.run_relap5(rel, timeout=900)
        m = re.search(r"输出=(\S+)", msg)
        if not (m and "正常结束=True" in msg):
            P(f"  {t['task_id']:24s} 未跑通，跳过")
            continue
        txt = R._read_o(R._SB.resolve(m.group(1)))
        # L2：各体末两点 tempf 的相对变化之最大
        ser = get_series(txt, "tempf")
        worst = 0.0
        for cid, pts in ser.items():
            if len(pts) >= 2:
                a, b = pts[-2][1], pts[-1][1]
                worst = max(worst, abs(b - a) / (abs(b) or 1.0))
        if ser:
            drifts.append((t["task_id"], fam, worst))
        # L3a：两相体的 |tempf - Tsat(p)|
        sp, sv = get_series(txt, "pressure"), get_series(txt, "voidg")
        for cid in set(sp) & set(sv) & set(ser):
            pi, vg, tf = last(sp, cid), last(sv, cid), last(ser, cid)
            if pi and vg is not None and 0.02 < vg < 0.98 and tf is not None:
                ts_ = sat_temp_K(pi)
                if ts_ == ts_:
                    sats.append((t["task_id"], fam, cid, abs(tf - ts_)))
        P(f"  {t['task_id']:24s} 收敛余量(末两点)={worst:.5f}")


def pct(xs, tag):
    if not xs:
        P(f"  {tag}: 无样本")
        return
    xs = sorted(xs)
    def q(p):
        return xs[min(len(xs) - 1, int(p * len(xs)))]
    P(f"  {tag}: n={len(xs)} 中位={st.median(xs):.5g} p90={q(.9):.5g} "
      f"p99={q(.99):.5g} 最大={xs[-1]:.5g}")


P("")
P("=" * 64)
P("L2 收敛余量（末两点 tempf 相对变化，参考解）")
P("=" * 64)
pct([d for _, _, d in drifts], "全部")
for fam in sorted(set(f for _, f, _ in drifts)):
    pct([d for _, f, d in drifts if f == fam], fam)

P("")
P("=" * 64)
P("L3a 饱和一致性余量 |tempf − Tsat(p)|（两相体，参考解，单位 K）")
P("=" * 64)
pct([s for *_, s in sats], "全部")
if sats:
    P("  最大值样本：")
    for tid, fam, cid, s in sorted(sats, key=lambda x: -x[3])[:5]:
        P(f"    {tid:24s} {fam:16s} {cid}  {s:.2f} K")

open(OUT, "w", encoding="utf-8").write("\n".join(buf))
print("->", OUT)
