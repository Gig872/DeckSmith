# -*- coding: utf-8 -*-
"""从已有结果标定 L3 判据阈值（不烧 token）。

思路：阈值 = 已知良好（参考解）分布与已知失效（agent 结果）分布之间的间隙。
  L3a 饱和一致性：两相时 |tempf − Tsat(P)| 的分布
  L3b 能量平衡  ：|Q − ṁ·cp·(Tout − Tin)| / Q 的分布（仅单相点）
"""
from __future__ import annotations

import glob
import json
import os
import statistics as st
import sys

ROOT = r"C:\relap-5\agent-kit"
BENCH = os.path.join(ROOT, "bench")
sys.path.insert(0, ROOT)
sys.path.insert(0, BENCH)
from postprocess.water import sat_temp_K, cp_liquid  # noqa: E402

OUT = r"C:\relap-5\论文\_calib_l3.txt"
buf = []
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass


def P(*a):
    s = " ".join(str(x) for x in a)
    buf.append(s)
    print(s)


def load(p):
    rows = []
    if os.path.isfile(p):
        for line in open(p, encoding="utf-8"):
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def pick(sc: dict, var: str):
    for k, v in (sc or {}).items():
        if k.startswith(var + ":"):
            return v
    return None


FAM_TIN = {"single_pipe_steady": 300.0, "chf_dryout": 500.0, "hs_gap": 560.0,
           "point_kinetics": 560.0, "numerical_grid": 300.0}
FAM_P = {"hs_gap": 15.5e6, "chf_dryout": 5.0e6, "point_kinetics": 15.0e6}

tasks = {t["task_id"]: t for t in load(os.path.join(BENCH, "tasks.jsonl"))}
ex = {r["task_id"]: r for r in load(os.path.join(BENCH, "expected.jsonl"))}
run = []
for p in sorted(glob.glob(os.path.join(BENCH, "run_results*.jsonl"))):
    run += load(p)
run_last = {}
for r in run:
    run_last[r["task_id"]] = r


def margins(sc, t):
    """返回 (饱和余量, 能量余量)，任一不可算则为 None。"""
    fam = t["family"]
    prm = t.get("params") or {}
    tempf = pick(sc, "tempf")
    voidg = pick(sc, "voidg")
    Pp = pick(sc, "pressure") or FAM_P.get(fam)
    sat = None
    if tempf is not None and voidg is not None and Pp and 0.02 < voidg < 0.98:
        sat = abs(tempf - sat_temp_K(Pp))
    en = None
    Q = prm.get("power")
    m = prm.get("mdot")
    Tin = FAM_TIN.get(fam)
    if tempf is not None and Q and m and Tin and (voidg is None or voidg < 0.02):
        cp = cp_liquid((Tin + tempf) / 2.0)          # kJ/(kg·K)
        en = abs(Q - m * cp * 1000.0 * (tempf - Tin)) / Q
    return sat, en


def pct(xs):
    if not xs:
        return "—"
    xs = sorted(xs)
    def q(p):
        return xs[min(len(xs) - 1, int(p * len(xs)))]
    return (f"n={len(xs)} 中位={st.median(xs):.4g} p90={q(.9):.4g} "
            f"p99={q(.99):.4g} 最大={xs[-1]:.4g}")


P("=" * 64)
P("L3a 饱和一致性余量 |tempf − Tsat(P)|  （两相点，单位 K）")
P("=" * 64)
ref_sat, run_sat, bad_sat = [], [], []
for tid, r in ex.items():
    if not r.get("valid"):
        continue
    s, _ = margins(r.get("scalars") or {}, tasks[tid])
    if s is not None:
        ref_sat.append(s)
for tid, r in run_last.items():
    if tid not in ex or not ex[tid].get("valid"):
        continue
    s, _ = margins(r.get("scalars") or {}, tasks[tid])
    if s is not None:
        run_sat.append(s)
        if not r.get("phys_ok"):
            bad_sat.append(s)
P("  参考解(应通过)   :", pct(ref_sat))
P("  agent 结果       :", pct(run_sat))
P("  其中物理不自洽   :", (f"n={len(bad_sat)} 值={[round(x,2) for x in bad_sat]}" if bad_sat else "无"))

P("")
P("=" * 64)
P("L3b 能量平衡余量 |Q − ṁ·cp·ΔT| / Q  （单相点，无量纲）")
P("=" * 64)
ref_en, run_en, bad_en = [], [], []
for tid, r in ex.items():
    if not r.get("valid"):
        continue
    _, e = margins(r.get("scalars") or {}, tasks[tid])
    if e is not None:
        ref_en.append(e)
for tid, r in run_last.items():
    if tid not in ex or not ex[tid].get("valid"):
        continue
    _, e = margins(r.get("scalars") or {}, tasks[tid])
    if e is not None:
        run_en.append(e)
        if not r.get("phys_ok"):
            bad_en.append(e)
P("  参考解(应通过)   :", pct(ref_en))
P("  agent 结果       :", pct(run_en))
P("  其中物理不自洽   :", (f"n={len(bad_en)} 值={[round(x,4) for x in bad_en]}" if bad_en else "无"))

# agent 判为物理不自洽的题，直接看其标量是否可算
P("")
P("=" * 64)
P("物理不自洽的 agent 记录（全部族）")
P("=" * 64)
n = 0
for tid, r in run_last.items():
    if r.get("exec_ok") and not r.get("phys_ok"):
        n += 1
        s, e = margins(r.get("scalars") or {}, tasks[tid])
        P(f"  {tid:24s} fam={tasks[tid]['family']:18s} 饱和余量={s} 能量余量={e}")
P(f"  共 {n} 例")

P("")
P("=" * 64)
P("L3b 阈值影响：按能量余量分档 × 当前分类（agent 结果）")
P("=" * 64)
bands = [(0.0, 0.05), (0.05, 0.10), (0.10, 0.25), (0.25, 9.9)]
tab = {b: {"结构失": 0, "物理失": 0, "语义失": 0, "完全通过": 0} for b in bands}
tot = {b: 0 for b in bands}
for tid, r in run_last.items():
    if tid not in ex or not ex[tid].get("valid"):
        continue
    _, e = margins(r.get("scalars") or {}, tasks[tid])
    if e is None:
        continue
    for lo, hi in bands:
        if lo <= e < hi:
            tot[(lo, hi)] += 1
            if not r.get("exec_ok"):
                tab[(lo, hi)]["结构失"] += 1
            elif not r.get("phys_ok"):
                tab[(lo, hi)]["物理失"] += 1
            elif not r.get("sem_ok"):
                tab[(lo, hi)]["语义失"] += 1
            else:
                tab[(lo, hi)]["完全通过"] += 1
            break
P(f"  {'能量余量':>14s} {'N':>4s} {'结构失':>6s} {'物理失':>6s} {'语义失':>6s} {'完全通过':>8s}")
for b in bands:
    lo, hi = b
    label = f"[{lo:.2f},{hi:.2f})"
    P(f"  {label:>14s} {tot[b]:4d} {tab[b]['结构失']:6d} {tab[b]['物理失']:6d} "
      f"{tab[b]['语义失']:6d} {tab[b]['完全通过']:8d}")
P("  读法：若把阈值收紧到 0.10，则 [0.10,0.25) 档中当前‘语义失/完全通过’的题将转判为物理失。")

open(OUT, "w", encoding="utf-8").write("\n".join(buf))
print("\n->", OUT)
