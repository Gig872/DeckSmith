# -*- coding: utf-8 -*-
"""reextract：**不调 LLM**，用本地重跑"智能体已产出的卡"来重算关键标量（口径修正后使用）。

用法： python bench/reextract.py
会就地更新 bench/run_results*.jsonl 的 exec_ok / phys_ok / scalars / sem_ok。
产出卡不存在（已被清理）的样本会标记 reextract=missing，保留原值。
"""
from __future__ import annotations

import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import tools.relap5 as R  # noqa: E402
from bench.agg import compare, scalars  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    tasks = {json.loads(l)["task_id"]: json.loads(l)
             for l in open(os.path.join(HERE, "tasks.jsonl"), encoding="utf-8")}
    exp = {json.loads(l)["task_id"]: json.loads(l)
           for l in open(os.path.join(HERE, "expected.jsonl"), encoding="utf-8")}
    n_ok = n_missing = 0
    for p in glob.glob(os.path.join(HERE, "run_results*.jsonl")):
        rows = [json.loads(l) for l in open(p, encoding="utf-8")]
        for r in rows:
            t = tasks.get(r["task_id"])
            prod = r.get("produced")
            if not t or not prod:
                continue
            pth = R._SB.resolve(prod)
            if not pth.is_file():
                r["reextract"] = "missing"
                n_missing += 1
                continue
            msg = R.run_relap5(prod, timeout=600)
            if "正常结束=True" in msg:
                m = re.search(r"输出=(\S+)", msg)
                if m:
                    txt = R._read_o(R._SB.resolve(m.group(1)))
                    r["exec_ok"] = True
                    r["scalars"] = scalars(txt, t.get("key_outputs") or [])
                    san = R.check_sanity(m.group(1))
                    r["phys_ok"] = R.sanity_passes(san)   # 统一判据
                    r["reextract"] = "ok"
                    n_ok += 1
            else:
                r["exec_ok"] = False
                r["phys_ok"] = False
                r["reextract"] = "fail"
            e = exp.get(r["task_id"]) or {}
            r["expected"] = e.get("scalars") or {}
            r["sem_ok"] = bool(r.get("scalars")) and compare(
                r["scalars"], r["expected"], t.get("key_outputs") or [])
        with open(p, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"reextract 完成：重算 {n_ok}，产出卡缺失 {n_missing}")


if __name__ == "__main__":
    main()
