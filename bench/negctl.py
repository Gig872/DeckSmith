# -*- coding: utf-8 -*-
r"""判定器负对照实验（零 token，只跑本地 RELAP5）。

三组：
  P   正对照：本题的**参考解卡**            → 期望 exec∧phys∧sem 全通过（测**误报率**）
  N1  负对照：**同族另一题**的参考解卡      → 期望 exec∧phys 通过、**sem 必须失败**（测**漏报率**）
  N2  负对照：本题卡**删掉终止卡**          → 期望**结构失效**（测结构层检出）

并发：**每个分片一个独立 workspace**（RELAP5 会在 cwd 里删建临时文件，共用会互相踩踏）。
用法：
  python n3_negctl.py --shard 0 --nshards 4 [--limit N] [--no-N2]
  python n3_negctl.py --nshards 4              # 驱动：并行起 4 个分片
"""
from __future__ import annotations

import argparse, io, json, os, subprocess, sys, time

ROOT = r"C:\relap-5\agent-kit"
HERE = os.path.join(ROOT, "bench")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)
if HERE not in sys.path:
    sys.path.insert(0, HERE)

OUTD = r"C:\relap-5\_audit\n3_out"
os.makedirs(OUTD, exist_ok=True)

L3_POLICY = {
    "accumulator":    {"sat": False, "energy": True},
    "chf_dryout":     {"sat": False, "energy": False},
    "lof_transient":  {"sat": False, "energy": False},
    "point_kinetics": {"sat": False, "energy": False},
    "hs_gap":         {"sat": True,  "energy": False},
    "modify_model":   {"sat": True,  "energy": False},
}


def load_all():
    tasks, exp = {}, {}
    for line in io.open(os.path.join(HERE, "tasks.jsonl"), encoding="utf-8"):
        if line.strip():
            t = json.loads(line); tasks[t["task_id"]] = t
    for line in io.open(os.path.join(HERE, "expected.jsonl"), encoding="utf-8"):
        if line.strip():
            e = json.loads(line); exp[e["task_id"]] = e
    return tasks, exp


def judge(R, agg, verify, rel, task, exp_scalars, tag):
    rec = {"case": tag, "task_id": task["task_id"], "family": task.get("family"),
           "exec_ok": False, "phys_ok": False, "sem_ok": False,
           "timeout": False, "n_errors": None, "l3_doubt": None, "note": ""}
    p = R._SB.resolve(rel)
    if not p.is_file():
        rec["note"] = "卡不存在"; return rec
    text = p.read_text(encoding="utf-8", errors="replace")
    rec["l1_ok"] = "通过" in (R.validate_i(text) or "")
    msg = R.run_relap5(rel, timeout=900)
    if "运行超时" in msg:
        rec["timeout"] = True; rec["note"] = "timeout"; return rec
    rec["exec_ok"] = "正常结束=True" in msg
    import re as _re
    m = _re.search(r"输出=(\S+)", msg)
    if not (rec["exec_ok"] and m):
        rec["note"] = msg[:80]; return rec
    o = m.group(1)
    otxt = R._read_o(R._SB.resolve(o))
    mm = _re.search(r"错误数=(\d+)", R.parse_output(o))
    rec["n_errors"] = int(mm.group(1)) if mm else None
    san_ok = R.sanity_passes(R.check_sanity(o))
    pol = L3_POLICY.get(task.get("family", ""), {"sat": True, "energy": True})
    prm = task.get("params") or {}
    ver_ok = True
    try:
        va = verify.assess(o, power=prm.get("power"), mdot=prm.get("mdot"),
                           sat=pol["sat"], energy=pol["energy"])
        rec["l3_doubt"] = va["n_doubt"]
        ver_ok = (va["n_doubt"] == 0)
    except Exception as e:
        rec["note"] = "L3异常:%s" % str(e)[:50]
    rec["phys_ok"] = bool(san_ok and ver_ok)
    sc = agg.scalars(otxt, task.get("key_outputs") or [])
    rec["sem_ok"] = agg.compare(sc, exp_scalars, task.get("key_outputs") or [])
    return rec


def nearest_sibling(t, sibs, tasks):
    """选参数最接近的兄弟（差得最少者最难抓）。"""
    p0 = t.get("params") or {}
    best, bs = None, None
    for s in sibs:
        p1 = tasks[s].get("params") or {}
        keys = set(p0) | set(p1)
        ndiff = sum(1 for k in keys if p0.get(k) != p1.get(k))
        # 归一化幅度（仅数值可比项）
        mag = 0.0
        for k in keys:
            a, b = p0.get(k), p1.get(k)
            if isinstance(a, (int, float)) and isinstance(b, (int, float)):
                mag += abs(a - b) / (abs(a) + abs(b) + 1e-9)
        sc = (ndiff, round(mag, 6))
        if bs is None or sc < bs:
            bs = sc; best = s
    return best


def run_shard(k, n, limit, do_N2, nearest=False):
    WS = os.path.join(ROOT, "workspace_negctl", "w%d" % k)
    os.makedirs(WS, exist_ok=True)
    os.environ["AGENT_WORKSPACE"] = WS
    os.environ.setdefault("AGENT_LEARNED_DIR", os.path.join(WS, "learned"))
    import registry; registry.load_plugins("tools")
    import tools.relap5 as R
    from bench import agg
    from tools import verify

    tasks, exp = load_all()
    valid = {tid for tid, e in exp.items() if e.get("valid")}
    ids = sorted(valid & set(tasks))
    if limit:
        ids = ids[:limit]
    byfam = {}
    for tid in ids:
        byfam.setdefault(tasks[tid]["family"], []).append(tid)

    out = os.path.join(OUTD, "raw_shard%d.jsonl" % k)
    f = io.open(out, "a", encoding="utf-8")
    t0 = time.time()
    todo = [tid for i, tid in enumerate(ids) if i % n == k]
    print("shard %d/%d：%d 题，workspace=%s" % (k, n, len(todo), WS), flush=True)
    for j, tid in enumerate(todo, 1):
        t = tasks[tid]
        es = (exp.get(tid) or {}).get("scalars", {})
        # P
        relP = "%s_P.i" % tid
        R._SB.resolve(relP).write_text(t["reference"], encoding="utf-8")
        f.write(json.dumps(judge(R, agg, verify, relP, t, es, "P"), ensure_ascii=False) + "\n")
        # N1：同族兄弟
        sibs = [x for x in byfam[t["family"]] if x != tid]
        if sibs:
            sib = nearest_sibling(t, sibs, tasks) if nearest else sibs[j % len(sibs)]
            relN1 = "%s_N1.i" % tid
            R._SB.resolve(relN1).write_text(tasks[sib]["reference"], encoding="utf-8")
            r = judge(R, agg, verify, relN1, t, es, "N1")
            r["sibling"] = sib
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
        # N2：删终止卡
        if do_N2:
            lines = t["reference"].rstrip("\n").split("\n")
            if lines and lines[-1].strip() == ".":
                lines = lines[:-1]
            relN2 = "%s_N2.i" % tid
            R._SB.resolve(relN2).write_text("\n".join(lines) + "\n", encoding="utf-8")
            f.write(json.dumps(judge(R, agg, verify, relN2, t, es, "N2"), ensure_ascii=False) + "\n")
        f.flush()
        if j % 10 == 0:
            print("  [%d/%d] %.0fs" % (j, len(todo), time.time() - t0), flush=True)
    f.close()
    print("shard %d 完成：%d 题，%.0fs" % (k, len(todo), time.time() - t0), flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--shard", type=int, default=-1)
    ap.add_argument("--nshards", type=int, default=4)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--no-N2", action="store_true")
    ap.add_argument("--nearest", action="store_true")
    a = ap.parse_args()
    if a.shard >= 0:
        run_shard(a.shard, a.nshards, a.limit, not a.no_N2, a.nearest)
        return
    procs = []
    for k in range(a.nshards):
        pf = io.open(os.path.join(OUTD, "shard%d.log" % k), "w", encoding="utf-8")
        cmd = [sys.executable, os.path.abspath(__file__), "--shard", str(k),
               "--nshards", str(a.nshards), "--limit", str(a.limit)]
        if a.no_N2:
            cmd.append("--no-N2")
        if a.nearest:
            cmd.append("--nearest")
        procs.append((k, subprocess.Popen(cmd, stdout=pf, stderr=subprocess.STDOUT), pf))
    print("已启动 %d 个分片" % a.nshards)
    for k, p, pf in procs:
        p.wait(); pf.close()
        print("分片 %d 结束 rc=%s" % (k, p.returncode))


if __name__ == "__main__":
    main()
