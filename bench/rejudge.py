# -*- coding: utf-8 -*-
"""免费重判：L3 判据修正后，用**已有的产物卡**重跑 + 重评估，不重跑 LLM。

用法： python bench/rejudge.py --cond on
产出： bench/run_results_k{cond}.jsonl（并把原 w*.jsonl 移入 archive/ 备份）
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import sys
import time

ROOT = r"C:\relap-5\agent-kit"
BENCH = os.path.join(ROOT, "bench")
os.environ.setdefault("AGENT_WORKSPACE", os.path.join(ROOT, "workspace_rejudge"))
sys.path.insert(0, ROOT)
sys.path.insert(0, BENCH)
import registry  # noqa: E402
registry.load_plugins("tools")
import tools.relap5 as R  # noqa: E402
from bench.agg import compare, scalars  # noqa: E402
from bench.harness import L3B_EXCLUDED  # noqa: E402
from tools.verify import assess  # noqa: E402

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass

TASKS = {}
TASK_ORDER = {}
for _i, _l in enumerate(open(os.path.join(BENCH, "tasks.jsonl"), encoding="utf-8")):
    try:
        _t = json.loads(_l)
        TASKS[_t["task_id"]] = _t
        TASK_ORDER[_t["task_id"]] = _i
    except Exception:
        pass

NWORKERS = 4   # runner --workers 4；sel 为全量序号 → worker = 序号 % 4


def find_deck(task_id, produced, cond):
    """按 runner 的分派规则（worker = 任务序号 % 4）精确定位产物卡。
    注意：产物卡跨 worker **大量重名**（同名可达 16 份），绝不能按文件名乱找。"""
    if not produced:
        return None
    cands = []
    idx = TASK_ORDER.get(task_id)
    if idx is not None:
        cands.append(os.path.join(ROOT, f"workspace_k{cond}_w{idx % NWORKERS}", produced))
    cands.append(os.path.join(ROOT, "workspace", "serial", produced))
    for p in cands:
        if os.path.isfile(p):
            return p
    return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cond", default="on")
    a = ap.parse_args()
    srcs = sorted(glob.glob(os.path.join(BENCH, f"run_results_k{a.cond}_w*.jsonl")))
    if not srcs:
        print("无源文件:", f"run_results_k{a.cond}_w*.jsonl")
        return
    rows = []
    for p in srcs:
        for line in open(p, encoding="utf-8"):
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    last = {}
    for r in rows:
        last[r["task_id"]] = r
    recs = list(last.values())
    print(f"待重判 {len(recs)} 条（来自 {len(srcs)} 个文件）")

    n_found = n_changed = 0
    for r in recs:
        deck = r.get("produced_abs") or ""
        if not (deck and os.path.isfile(deck)):
            deck = find_deck(r["task_id"], r.get("produced"), a.cond)
        if not deck:
            continue
        n_found += 1
        text = open(deck, encoding="utf-8", errors="replace").read()
        rel = f"rj_{r['task_id']}.i"
        R._SB.resolve(rel).write_text(text, encoding="utf-8")
        msg = R.run_relap5(rel, timeout=900)
        old = bool(r.get("phys_ok"))
        if "运行超时" in msg:
            r["timeout"] = True
            r["phys_ok"] = False
            continue
        if "正常结束=True" not in msg:
            r["exec_ok"] = False
            r["phys_ok"] = False
            if old != r["phys_ok"]:
                n_changed += 1
            continue
        m = re.search(r"输出=(\S+)", msg)
        o = m.group(1)
        san = R.check_sanity(o)
        sanity_ok = R.sanity_passes(san)          # 统一判据
        prm = (TASKS.get(r["task_id"]) or {}).get("params") or {}
        va = assess(o, power=prm.get("power"), mdot=prm.get("mdot"),
                    sat=(r["family"] not in L3B_EXCLUDED))
        r["l3_doubt"] = va["n_doubt"]
        r["l3_sat_max_k"] = va["sat_max_margin"]
        r["l3_energy_pct"] = va["energy_rel_pct"]
        r["l3_sat_applicable"] = r["family"] not in L3B_EXCLUDED
        r["check_sanity"] = san.splitlines()[0] if san else ""
        r["phys_ok"] = bool(sanity_ok and va["n_doubt"] == 0)
        if old != r["phys_ok"]:
            n_changed += 1

    stamp = time.strftime("%Y%m%d_%H%M%S")
    arch = os.path.join(BENCH, "archive", stamp + "_rejudge_src")
    os.makedirs(arch, exist_ok=True)
    for p in srcs:
        shutil.move(p, os.path.join(arch, os.path.basename(p)))
    out = os.path.join(BENCH, f"run_results_k{a.cond}.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"找到产物卡 {n_found}/{len(recs)}；物理判定改变 {n_changed} 条")
    print("重判结果 ->", out)
    print("原文件备份 ->", arch)


if __name__ == "__main__":
    main()
