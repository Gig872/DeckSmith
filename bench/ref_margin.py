# -*- coding: utf-8 -*-
r"""提取全部有效参考解的 L3 余量（饱和温度余量 / 能量偏差）。

只跑本地 RELAP5，不调用任何语言模型，不消耗 token。
多进程分片：每个分片一个独立工作目录，避免 relap5_cwd 互删临时文件。

用法：
  python bench/ref_margin.py --nshards 4            # 启动 4 个分片
  python bench/ref_margin.py --shard 0 --nshards 4  # 单分片（内部用）

输出：bench/ref_margin_shard{k}.jsonl（追加写，可断点续跑）
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT_PAT = os.path.join(HERE, "ref_margin_shard%d.jsonl")


def load_all():
    tasks = [json.loads(l) for l in
             open(os.path.join(HERE, "tasks.jsonl"), encoding="utf-8")]
    exp = {}
    for line in open(os.path.join(HERE, "expected.jsonl"), encoding="utf-8"):
        try:
            r = json.loads(line)
            exp[r["task_id"]] = r
        except Exception:  # noqa: BLE001
            pass
    return tasks, exp


def shard(k, n):
    ws = os.path.join(ROOT, "workspace_refmargin", "w%d" % k)
    os.makedirs(ws, exist_ok=True)
    os.environ["AGENT_WORKSPACE"] = ws          # 必须在 import tools 之前
    os.environ.setdefault("AGENT_LEARNED_DIR", os.path.join(ws, "learned"))
    sys.path.insert(0, ROOT)
    sys.path.insert(0, HERE)

    import registry  # noqa: E402
    registry.load_plugins("tools")
    import tools.relap5 as R  # noqa: E402
    from tools.verify import assess  # noqa: E402

    tasks, exp = load_all()
    out = OUT_PAT % k
    done = set()
    if os.path.exists(out):
        for line in open(out, encoding="utf-8"):
            try:
                done.add(json.loads(line)["task_id"])
            except Exception:  # noqa: BLE001
                pass

    todo = []
    for i, t in enumerate(tasks):
        if i % n != k:
            continue
        if not exp.get(t["task_id"], {}).get("valid"):
            continue
        if t["task_id"] in done:
            continue
        todo.append(t)

    print("shard %d/%d：待跑 %d 题" % (k, n, len(todo)), flush=True)
    f = open(out, "a", encoding="utf-8")
    t0 = time.time()
    for j, t in enumerate(todo, 1):
        p = t.get("params") or {}
        rel = "cal_%s.i" % t["task_id"]
        rec = {"task_id": t["task_id"], "family": t.get("family"),
               "task_type": t.get("task_type"), "ran": False,
               "sat_max_k": None, "energy_pct": None, "note": ""}
        try:
            R._SB.resolve(rel).write_text(t["reference"], encoding="utf-8")
            msg = R.run_relap5(rel, timeout=600)
            m = re.search(r"输出=(\S+)", msg)
            rec["ran"] = bool(m and "正常结束=True" in msg)
            if rec["ran"]:
                a = assess(m.group(1), power=p.get("power"), mdot=p.get("mdot"),
                           tin=p.get("tin"))
                rec["sat_max_k"] = a.get("sat_max_margin")
                rec["energy_pct"] = a.get("energy_rel_pct")
            else:
                rec["note"] = msg[:160]
        except Exception as e:  # noqa: BLE001
            rec["note"] = "异常: %s" % e
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
        print("w%d [%d/%d] %-26s ran=%s sat=%s energy=%s (%.0fs)"
              % (k, j, len(todo), t["task_id"], rec["ran"],
                 rec["sat_max_k"], rec["energy_pct"], time.time() - t0), flush=True)
    f.close()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=-1)
    ap.add_argument("--nshards", type=int, default=4)
    a = ap.parse_args()
    if a.shard >= 0:
        shard(a.shard, a.nshards)
        return
    procs = []
    for k in range(a.nshards):
        pf = open(os.path.join(HERE, "ref_margin_w%d.log" % k), "w", encoding="utf-8")
        cmd = [sys.executable, os.path.abspath(__file__),
               "--shard", str(k), "--nshards", str(a.nshards)]
        procs.append((k, subprocess.Popen(cmd, stdout=pf, stderr=subprocess.STDOUT), pf))
    print("已启动 %d 个分片，日志 bench/ref_margin_w*.log" % a.nshards)
    for k, p, pf in procs:
        p.wait()
        pf.close()
        print("分片 %d 结束 rc=%s" % (k, p.returncode))


if __name__ == "__main__":
    main()
