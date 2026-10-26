# -*- coding: utf-8 -*-
"""metrics：按论文式(7)–(12) 计算指标并出表。

用法： python bench/metrics.py            # 用 bench/run_results.jsonl
"""
from __future__ import annotations

import json
import os
import statistics as st
import sys
from collections import defaultdict

try:                                   # 控制台/重定向为 GBK 时也能打印
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "run_results.jsonl")
EXP = os.path.join(HERE, "expected.jsonl")


def load(path):
    rows = []
    if os.path.isfile(path):
        for line in open(path, encoding="utf-8"):
            try:
                rows.append(json.loads(line))
            except Exception:  # noqa: BLE001
                pass
    return rows


def load_results(knowledge=None, tag=None):
    """读取本轮结果。

    knowledge = 'on'/'off'/None：按**评测条件**过滤（带库/无库）。
    tag       = ''/'_kappa'/'_half'/'_oral'/…/None：按**批次标签**过滤。
    **两者必须合用**：A、κ、探针同为 on，只按 knowledge 过滤会四批混算。"""
    import glob
    rows = []
    for p in sorted(glob.glob(os.path.join(HERE, "run_results*.jsonl"))):
        for r in load(p):
            if knowledge in ("on", "off"):
                if str(r.get("knowledge") or "").lower() != knowledge:
                    continue
            if tag is not None:
                if str(r.get("tag") or "") != tag:
                    continue
            rows.append(r)
    return rows


def detect_conditions() -> dict:
    """本轮结果里各评测条件的题数，用于提示漏加 --knowledge。"""
    import glob
    c = {}
    for p in sorted(glob.glob(os.path.join(HERE, "run_results*.jsonl"))):
        for r in load(p):
            k = str(r.get("knowledge") or "(无字段)")
            c[k] = c.get(k, 0) + 1
    return c


def load_key_outputs():
    ko = {}
    tp = os.path.join(HERE, "tasks.jsonl")
    if os.path.isfile(tp):
        for line in open(tp, encoding="utf-8"):
            try:
                t = json.loads(line)
                ko[t["task_id"]] = t.get("key_outputs") or []
            except Exception:  # noqa: BLE001
                pass
    return ko


def _legacy_key(k: str):
    """旧口径键名回退（用于重评归档结果）：
       peak:/trough: 与旧 max/maxabs/min 数值等价；
       last: 在单调趋稳的稳态题上与旧 max/min/maxabs 近似等价。"""
    var, _, agg = k.partition(":")
    for pre in ("peak:", "trough:"):
        if agg.startswith(pre):
            return f"{var}:{agg.split(':', 1)[1]}"
    if agg.startswith("last:"):
        return f"{var}:{agg.split(':', 1)[1]}"
    return None


def _pick(scal: dict, k: str):
    v = scal.get(k)
    if v is None:
        lk = _legacy_key(k)
        if lk:
            v = scal.get(lk)
    return v


def _cmp(scal, exp, key_outputs):
    """按最新真值重算行为等价（避免 expected.jsonl 更新后指标失真）。"""
    if not exp or not scal:
        return False
    for spec in key_outputs:
        k = f'{spec["var"]}:{spec.get("agg", "max")}'
        x, y = _pick(scal, k), exp.get(k)
        if x is None or y is None:
            return False
        tol, mode = spec.get("tol", 0.05), spec.get("mode", "rel")
        if mode == "rel":
            if abs(x - y) / (abs(y) or 1.0) > tol:
                return False
        elif abs(x - y) > tol:
            return False
    return True


def rate(rows, pred):
    return (sum(1 for r in rows if pred(r)) / len(rows)) if rows else 0.0


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--knowledge", choices=["on", "off"], default=None,
                    help="只看某一评测条件（带库/无库）")
    ap.add_argument("--tag", default=None,
                    help="只看某一批次标签：''=主实验，_kappa=稳定性，_half/_oral=语域探针")
    ap.add_argument("--exclude-timeout", action="store_true",
                    help="把运行超时的题剔出分母（默认计入）")
    args = ap.parse_args()

    conds = detect_conditions()
    if args.knowledge is None and len([k for k in conds]) > 1:
        print(f"[警告] 同时存在多种评测条件 {conds}；建议加 --knowledge on|off 分别出表。")
    if args.tag is None:
        print("[提示] 未指定 --tag：A / κ / 探针 等同为 on 的批次会被混算。"
              "主实验请用 --tag ''")
    rows = load_results(args.knowledge, args.tag)
    if not rows:
        print("没有 run_results*.jsonl（先跑 bench/runner.py）")
        return
    # 有效性过滤：只统计参考卡本身有效的题（无效题不算 agent 的错）
    exps = {r["task_id"]: r for r in load(EXP)}
    valid_ids = {tid for tid, r in exps.items() if r.get("valid")}
    ko = load_key_outputs()
    # 按最新真值就地重算 sem（expected.jsonl 更新后无需重跑 agent）
    for r in rows:
        e = (exps.get(r["task_id"]) or {}).get("scalars", {})
        r["sem_ok"] = _cmp(r.get("scalars") or {}, e, ko.get(r["task_id"], []))
    rows = [r for r in rows if not valid_ids or r["task_id"] in valid_ids]
    if not rows:
        print("过滤后无样本（expected.jsonl 里没有 valid 的题）")
        return
    n_to_all = sum(1 for r in rows if r.get("timeout"))
    n_cr_all = sum(1 for r in rows if r.get("crashed"))
    if args.exclude_timeout:
        rows = [r for r in rows if not r.get("timeout")]

    # 每题取最后一次重复（可重复性另算）
    last = {}
    for r in rows:
        last[(r["task_id"], r.get("repeat", 1))] = r
    reps = defaultdict(list)
    for (tid, rep), r in last.items():
        reps[tid].append(r)
    first = [v[0] for v in reps.values()]

    R_exec = rate(first, lambda r: r["exec_ok"])
    R_phys = rate(first, lambda r: r["exec_ok"] and r["phys_ok"])
    R_sem = rate(first, lambda r: r["exec_ok"] and r["phys_ok"] and r["sem_ok"])
    judge_pass = [r for r in first if r["exec_ok"] and r["phys_ok"]]
    FNR = (rate(judge_pass, lambda r: not r["sem_ok"]) if judge_pass else 0.0)

    print("=" * 56)
    print(f"评测条件 knowledge = {args.knowledge or '(混合)'}")
    print(f"样本数 N = {len(first)}（已过滤无效参考题）")
    print(f"  超时 {sum(1 for r in first if r.get('timeout'))} 例；"
          f"崩溃 {sum(1 for r in first if r.get('crashed'))} 例；"
          f"总样本里超时 {n_to_all} 崩溃 {n_cr_all}"
          + ("（超时已剔除）" if args.exclude_timeout else "（超时计入分母）"))
    print(f"R_exec 终态可运行率 = {R_exec:.1%}")
    print(f"R_phys 物理通过率   = {R_phys:.1%}")
    print(f"R_sem  语义符合率   = {R_sem:.1%}")
    print(f"Δ(Exec,Phys) = {R_exec - R_phys:.1%}    Δ(Phys,Sem) = {R_phys - R_sem:.1%}")
    print(f"FNR 危险漏检率(判通过却语义错) = {FNR:.1%}")
    of = [r.get("exec_ok_first") for r in first if r.get("exec_ok_first") is not None]
    if of:
        print(f"R_exec(1) 首跑可运行率 = {sum(1 for x in of if x) / len(of):.1%}  (n={len(of)})")
    it = [r["iterations"] for r in first if r.get("iterations")]
    if it:
        print(f"自测轮次：均值 {st.mean(it):.2f}，中位 {st.median(it):.0f}，最大 {max(it)}")
    tk = [r["tokens"] for r in first if r.get("tokens")]
    if tk:
        print(f"tokens：均值 {st.mean(tk):,.0f}，合计 {sum(tk):,}")

    # 稳定性 κ：同题多次生成的失效判定是否全同
    if any(len(v) > 1 for v in reps.values()):
        agree = []
        for tid, v in reps.items():
            if len(v) > 1:
                sigs = {(bool(r["exec_ok"]), bool(r.get("phys_ok")), bool(r.get("sem_ok")))
                        for r in v}
                agree.append(1.0 if len(sigs) == 1 else 0.0)
        if agree:
            print(f"重复一致性 κ（同题多次判定全同的比例）= {st.mean(agree):.1%}  (n={len(agree)})")

    # 分族
    print("-" * 56)
    print(f"{'族':22s} {'N':>4s} {'R_exec':>7s} {'R_phys':>7s} {'R_sem':>7s}")
    byfam = defaultdict(list)
    for r in first:
        byfam[r["family"]].append(r)
    for fam, rs in sorted(byfam.items()):
        print(f"{fam:22s} {len(rs):4d} "
              f"{rate(rs, lambda r: r['exec_ok']):7.1%} "
              f"{rate(rs, lambda r: r['exec_ok'] and r['phys_ok']):7.1%} "
              f"{rate(rs, lambda r: r['sem_ok']):7.1%}")

    # 分任务类型
    print("-" * 56)
    bytt = defaultdict(list)
    for r in first:
        bytt[r["task_type"]].append(r)
    for tt, rs in sorted(bytt.items()):
        print(f"{tt:22s} N={len(rs):3d}  R_exec={rate(rs, lambda r: r['exec_ok']):.1%} "
              f"R_phys={rate(rs, lambda r: r['exec_ok'] and r['phys_ok']):.1%} "
              f"R_sem={rate(rs, lambda r: r['sem_ok']):.1%}")


if __name__ == "__main__":
    main()
