# -*- coding: utf-8 -*-
"""标定饱和一致性的**相态判定带**：不同 voidg 带下，参考解的 |tempf−Tsat| 分布。
   重跑参考解（本地，不烧 token），把逐体记录落盘供离线分析。"""
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

OUT = r"C:\relap-5\论文\_calib_sat.txt"
RAW = r"C:\relap-5\论文\_sat_raw.jsonl"
buf = []
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def P(*a):
    s = " ".join(str(x) for x in a)
    buf.append(s)
    print(s)


def last(ser, cid):
    pts = ser.get(cid)
    return pts[-1][1] if pts else None


FAMS = ["single_pipe_steady", "chf_dryout", "point_kinetics", "hs_gap", "critical_nozzle",
        "sbloca_blowdown", "numerical_grid"]
PER = 2
tasks = [json.loads(l) for l in open(os.path.join(BENCH, "tasks.jsonl"), encoding="utf-8")]
exp = {r["task_id"]: r for r in (json.loads(l) for l in
       open(os.path.join(BENCH, "expected.jsonl"), encoding="utf-8"))}
picked = {}
for t in tasks:
    if not exp.get(t["task_id"], {}).get("valid"):
        continue
    if t["family"] in FAMS and len(picked.setdefault(t["family"], [])) < PER:
        picked[t["family"]].append(t)

fraw = open(RAW, "w", encoding="utf-8")
nrun = 0
for fam, ts_ in sorted(picked.items()):
    for t in ts_:
        rel = f"csat_{t['task_id']}.i"
        R._SB.resolve(rel).write_text(t["reference"], encoding="utf-8")
        msg = R.run_relap5(rel, timeout=900)
        m = re.search(r"输出=(\S+)", msg)
        if not (m and "正常结束=True" in msg):
            continue
        nrun += 1
        txt = R._read_o(R._SB.resolve(m.group(1)))
        sp, stf, sv, stg = (get_series(txt, v) for v in
                            ("pressure", "tempf", "voidg", "tempg"))
        for cid in sorted(sp):
            p = last(sp, cid)
            if not p:
                continue
            vg = last(sv, cid) if sv.get(cid) else None
            tf = last(stf, cid) if stf.get(cid) else None
            tg = last(stg, cid) if stg.get(cid) else None
            ts = sat_temp_K(p)
            if ts != ts:
                continue
            rec = {"task": t["task_id"], "fam": fam, "cid": cid, "p": p,
                   "voidg": vg, "tempf": tf, "tempg": tg, "Tsat": ts}
            fraw.write(json.dumps(rec, ensure_ascii=False) + "\n")
fraw.close()
P(f"重跑参考解 {nrun} 次，逐体记录落盘 -> {RAW}")

recs = [json.loads(l) for l in open(RAW, encoding="utf-8")]
P(f"逐体记录 n={len(recs)}")
P("")
P("=" * 68)
P("不同相态判定带下，参考解的 |tempf − Tsat| 分布（应尽量小）")
P("=" * 68)
P(f"  {'voidg 带':>14s} {'n':>5s} {'中位':>9s} {'p90':>9s} {'p99':>9s} {'最大':>9s}")
for lo, hi in [(0.02, 0.98), (0.05, 0.95), (0.10, 0.90), (0.20, 0.80), (0.30, 0.70)]:
    xs = [abs(r["tempf"] - r["Tsat"]) for r in recs
          if r["voidg"] is not None and r["tempf"] is not None and lo <= r["voidg"] <= hi]
    if not xs:
        P(f"  [{lo:.2f},{hi:.2f})  无样本")
        continue
    xs = sorted(xs)
    q = lambda p: xs[min(len(xs) - 1, int(p * len(xs)))]
    P(f"  [{lo:.2f},{hi:.2f})  {len(xs):5d} {st.median(xs):9.2f} {q(.9):9.2f} "
      f"{q(.99):9.2f} {xs[-1]:9.2f}")

P("")
P("=" * 68)
P("过冷液检查：voidg 很小但 tempf 接近 Tsat 的体（真正的疑点）")
P("=" * 68)
sus = [r for r in recs if r["voidg"] is not None and r["voidg"] < 0.10
       and r["tempf"] is not None and (r["Tsat"] - r["tempf"]) < 5.0]
P(f"  voidg<0.10 且 (Tsat−tempf)<5K 的体：{len(sus)} 个")
for r in sus[:8]:
    P(f"    {r['task']:22s} {r['cid']} vg={r['voidg']:.3f} tempf={r['tempf']:.1f} "
      f"Tsat={r['Tsat']:.1f}")

open(OUT, "w", encoding="utf-8").write("\n".join(buf))
print("->", OUT)
