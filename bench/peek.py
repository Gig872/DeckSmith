# -*- coding: utf-8 -*-
"""用**最新真值**重新评估一组归档结果（不重跑 agent）。

用法： python bench/peek.py "bench/r1/run_results*.jsonl"
"""
from __future__ import annotations

import glob
import io
import json
import os
import sys
from collections import defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, HERE)

from metrics import _cmp, load, load_key_outputs  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass


def rate(rows, pred):
    return (sum(1 for r in rows if pred(r)) / len(rows)) if rows else 0.0


def main(pattern: str):
    exps = {r["task_id"]: r for r in load(os.path.join(HERE, "expected.jsonl"))}
    valid = {k for k, v in exps.items() if v.get("valid")}
    ko = load_key_outputs()

    rows = []
    for p in glob.glob(pattern):
        rows += load(p)
    for r in rows:
        e = (exps.get(r["task_id"]) or {}).get("scalars", {})
        r["sem_ok"] = _cmp(r.get("scalars") or {}, e, ko.get(r["task_id"], []))
    rows = [r for r in rows if r["task_id"] in valid]
    last = {}
    for r in rows:
        last[r["task_id"]] = r          # 每题取最后一次
    first = list(last.values())

    print(f"样本 N = {len(first)}")
    print(f"R_exec = {rate(first, lambda r: r['exec_ok']):.1%}")
    print(f"R_phys = {rate(first, lambda r: r['exec_ok'] and r['phys_ok']):.1%}")
    print(f"R_sem  = {rate(first, lambda r: r['sem_ok']):.1%}")
    jp = [r for r in first if r["exec_ok"] and r["phys_ok"]]
    print(f"FNR    = {rate(jp, lambda r: not r['sem_ok']):.1%}")
    print("-" * 52)
    print(f"{'族':22s}{'N':>4s}{'R_exec':>8s}{'R_phys':>8s}{'R_sem':>8s}")
    by = defaultdict(list)
    for r in first:
        by[r["family"]].append(r)
    for fam in sorted(by):
        rs = by[fam]
        print(f"{fam:22s}{len(rs):4d}"
              f"{rate(rs, lambda r: r['exec_ok']):8.1%}"
              f"{rate(rs, lambda r: r['exec_ok'] and r['phys_ok']):8.1%}"
              f"{rate(rs, lambda r: r['sem_ok']):8.1%}")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else os.path.join(HERE, "run_results*.jsonl"))
