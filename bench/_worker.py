# -*- coding: utf-8 -*-
r"""并发 worker：跑分配到的题目（独立工作目录），结果写到自己的 jsonl。

用法（由 runner.py --workers 调起）：
  python bench/_worker.py --indices 5,17,29 --workspace workspace\w1 --out bench\run_results_w1.jsonl
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--indices", required=True)
    ap.add_argument("--workspace", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--knowledge", choices=["on", "off", "off-strict"], default="off")
    ap.add_argument("--tag", default="")
    ap.add_argument("--resume", action="store_true",
                    help="断点续跑：跳过本 worker 输出文件里已完成的 (题目, 轮次)")
    ap.add_argument("--tasks", default="",
                    help="题库文件（默认 tasks.jsonl）。**必须与 runner 用同一份**，"
                         "否则索引会错位到别的题上——语域探针就踩过这个坑。")
    a = ap.parse_args()

    ws = os.path.join(ROOT, a.workspace)
    os.makedirs(ws, exist_ok=True)
    os.environ["AGENT_WORKSPACE"] = ws          # 必须在 import config/tools 之前设置
    # 评测隔离：本 worker 独占 learned 库，避免跨题累积污染
    os.environ.setdefault("AGENT_LEARNED_DIR", os.path.join(ws, "learned"))
    # 评测条件（带库/无库）——须在 import config/tools 之前装配
    from bench.evalenv import setup as _setup_eval  # noqa: E402
    _setup_eval(a.knowledge)

    import registry  # noqa: E402
    import tools.relap5 as R  # noqa: E402
    from bench.harness import evaluate, prepare, set_knowledge, set_tag  # noqa: E402
    from config import load  # noqa: E402
    from llm import OutOfCredit  # noqa: E402
    from bench.crashguard import mark_out_of_credit as _mark_out_of_credit  # noqa: E402

    set_knowledge(a.knowledge)
    set_tag(a.tag)

    registry.load_plugins("tools")
    s = load()
    prepare(ws)
    _tf = a.tasks or "tasks.jsonl"
    if not os.path.isabs(_tf):
        _tf = os.path.join(HERE, _tf)
    tasks = [json.loads(l) for l in open(_tf, encoding="utf-8")]
    exp = {}
    for line in open(os.path.join(HERE, "expected.jsonl"), encoding="utf-8"):
        try:
            r = json.loads(line)
            exp[r["task_id"]] = r
        except Exception:  # noqa: BLE001
            pass

    idxs = [int(x) for x in a.indices.split(",") if x.strip()]
    # 断点续跑：读本 worker 自己的输出文件，跳过已完成的 (题目, 轮次)。
    # 欠费中断或进程被杀后，用同一组参数重启即可接着跑，不会重复计费。
    done = set()
    if a.resume and os.path.isfile(a.out):
        for line in open(a.out, encoding="utf-8"):
            try:
                r = json.loads(line)
                done.add((r["task_id"], int(r.get("repeat") or 1)))
            except Exception:  # noqa: BLE001
                pass                      # 被杀时末行可能截断
        print(f"续跑：已完成 {len(done)} 条，跳过", flush=True)
    fout = open(a.out, "a", encoding="utf-8")
    t0 = time.time()
    for rep in range(1, a.repeats + 1):
        for i in idxs:
            t = tasks[i]
            if (t["task_id"], rep) in done:
                continue
            try:
                rec = evaluate(s, t, exp.get(t["task_id"]), rep)
            except OutOfCredit as e:
                # 欠费：本 worker 立即截断。断点仅落标记，不记成任务失败。
                _mark_out_of_credit(HERE, s.model, str(e))
                print(f"w{a.workspace[-3:]} 欠费截断，停止（已完成 {i} 之前的部分）", flush=True)
                fout.close()
                return
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            print(f"w{a.workspace[-3:]} [{i}] {t['task_id']:24s} exec={rec['exec_ok']} "
                  f"phys={rec['phys_ok']} sem={rec['sem_ok']} "
                  f"to={rec['timeout']} crash={rec['crashed']} ({time.time()-t0:.0f}s)", flush=True)
    fout.close()


if __name__ == "__main__":
    main()
