# -*- coding: utf-8 -*-
"""生成任务集：遍历各族的参数网格，产出 tasks.jsonl（每行一道任务）。

任务 = {task_id, family, params, nl(自然语言需求), reference(真值卡文本), key_outputs}
用法： python bench/gen.py
"""
from __future__ import annotations

import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bench.families import FAMILIES, TaskSpec  # noqa: E402
from bench.tasktypes import TT_FAMILIES  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tasks.jsonl")


def build() -> list[TaskSpec]:
    tasks = []
    for fam, (grid_fn, deck_fn) in FAMILIES.items():
        for i, p in enumerate(grid_fn(), 1):
            deck, nl, key = deck_fn(p)
            tasks.append(TaskSpec(f"{fam}_{i:04d}", fam, p, nl, deck, key))
    for _fam, fn in TT_FAMILIES.items():
        tasks.extend(fn())
    return tasks


def main() -> None:
    tasks = build()
    with open(OUT, "w", encoding="utf-8") as f:
        for t in tasks:
            f.write(json.dumps(t.__dict__, ensure_ascii=False) + "\n")
    fams = {}
    for t in tasks:
        fams[t.family] = fams.get(t.family, 0) + 1
    tt = {}
    for t in tasks:
        tt[t.task_type] = tt.get(t.task_type, 0) + 1
    print("tasks:", len(tasks), "| by family:", fams)
    print("by task_type:", tt)
    print("->", OUT)


if __name__ == "__main__":
    main()
