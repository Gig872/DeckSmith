# -*- coding: utf-8 -*-
"""reeval：参考卡修正后，用**新的期望值**重算已存结果的 sem_ok（无需重跑模型）。

只更新 sem_ok / expected 两栏；exec_ok / phys_ok 与参考卡无关，保持不变。
用法： python bench/reeval.py
"""
from __future__ import annotations

import glob
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bench.runner import compare  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    tasks = {json.loads(l)["task_id"]: json.loads(l)
             for l in open(os.path.join(HERE, "tasks.jsonl"), encoding="utf-8")}
    exp = {}
    for line in open(os.path.join(HERE, "expected.jsonl"), encoding="utf-8"):
        r = json.loads(line)
        exp[r["task_id"]] = r
    n_upd = 0
    for p in glob.glob(os.path.join(HERE, "run_results*.jsonl")):
        rows = [json.loads(l) for l in open(p, encoding="utf-8")]
        for r in rows:
            t = tasks.get(r["task_id"])
            e = exp.get(r["task_id"])
            if not t or not e:
                continue
            new_exp = e.get("scalars") or {}
            new_sem = bool(r.get("scalars")) and compare(r["scalars"], new_exp,
                                                         t.get("key_outputs") or [])
            if new_sem != r.get("sem_ok") or r.get("expected") != new_exp:
                n_upd += 1
            r["expected"] = new_exp
            r["sem_ok"] = new_sem
            r["ref_valid"] = e.get("valid")
        with open(p, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"reeval 完成，更新 {n_upd} 条")


if __name__ == "__main__":
    main()
