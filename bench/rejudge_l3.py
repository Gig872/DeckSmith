# -*- coding: utf-8 -*-
r"""用「全量参考解审计」得到的 L3 适用域，对主实验 A 的归档输入卡重新判分。

背景：原 L3_POLICY 是每族抽 3 个参考解得出的；对全部 324 个参考解审计后发现，
      另有 point_kinetics / hs_gap / modify_model 三族的参考解自身也超出判据，
      且 chf_dryout 的饱和判据同样被参考解突破。

本脚本只跑本地 RELAP5，不调用语言模型，零 token 成本。
输入：bench/decks_kon/<task_id>.i（主实验归档卡）
输出：bench/l3v2_shard{k}.jsonl

用法：
  python bench/rejudge_l3.py --nshards 4
  python bench/rejudge_l3.py --shard 0 --nshards 4
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import re
import shutil
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
DECKS = os.path.join(HERE, "decks_kon")
OUT_PAT = os.path.join(HERE, "l3v2_shard%d.jsonl")

# ---- 审计后的 L3 适用域（未列出的族：两条判据均适用）----
L3_POLICY_V2 = {
    "accumulator":   {"sat": False, "energy": True},    # 含非凝气体，相态判据失效
    "chf_dryout":    {"sat": False, "energy": False},   # 强沸腾：ΔT 触顶 + 稳态能量式不成立
    "lof_transient": {"sat": False, "energy": False},   # 强瞬态：两条判据均不成立
    "point_kinetics": {"sat": False, "energy": False},  # 点堆动力学：无热工控制体/稳态假设失效
    "hs_gap":        {"sat": True,  "energy": False},   # 含间隙热构件：稳态能量式不成立
    "modify_model":  {"sat": True,  "energy": False},   # 继承瞬态算例：稳态能量式不成立
}


def load_a(keep_keys=None):
    """主实验 A 的记录：去重规则＝优先 n_errors 非空；只取 repeat=1、tag="" 的题。"""
    def better(a, b):
        if a is None:
            return b
        if b is None:
            return a
        ra, rb = a.get("n_errors") is not None, b.get("n_errors") is not None
        if ra != rb:
            return a if ra else b
        return b

    rows = []
    for pat in ("run_results_kon_w*.jsonl", "run_results_kon.jsonl"):
        for p in glob.glob(os.path.join(HERE, pat)):
            for line in open(p, encoding="utf-8", errors="replace"):
                try:
                    rows.append(json.loads(line))
                except Exception:  # noqa: BLE001
                    pass
    u = {}
    for r in rows:
        if str(r.get("tag") or "") != "":
            continue
        k = (r["task_id"], r.get("repeat", 1))
        u[k] = better(u.get(k), r)
    out = {k: r for k, r in u.items() if k[1] == 1}
    if keep_keys:
        out = {k: r for k, r in out.items() if k[0] in keep_keys}
    return out


def shard(k, n):
    ws = os.path.join(ROOT, "workspace_l3v2", "w%d" % k)
    os.makedirs(ws, exist_ok=True)
    os.environ["AGENT_WORKSPACE"] = ws
    os.environ.setdefault("AGENT_LEARNED_DIR", os.path.join(ws, "learned"))
    sys.path.insert(0, ROOT)
    sys.path.insert(0, HERE)

    import registry  # noqa: E402
    registry.load_plugins("tools")
    import tools.relap5 as R  # noqa: E402
    from bench.agg import compare, scalars  # noqa: E402
    from tools.verify import assess  # noqa: E402

    tasks = {json.loads(l)["task_id"]: json.loads(l) for l in
             open(os.path.join(HERE, "tasks.jsonl"), encoding="utf-8")}
    A = load_a()
    todo = []
    for i, key in enumerate(sorted(A)):
        if i % n != k:
            continue
        tid = key[0]
        if os.path.isfile(os.path.join(DECKS, tid + ".i")):
            todo.append(tid)

    print("shard %d/%d：待重判 %d 题" % (k, n, len(todo)), flush=True)
    f = open(OUT_PAT % k, "a", encoding="utf-8")
    t0 = time.time()
    for j, tid in enumerate(todo, 1):
        old = A[(tid, 1)]
        t = tasks.get(tid) or {}
        rel = tid + ".i"
        shutil.copy2(os.path.join(DECKS, rel), os.path.join(ws, rel))
        pol = L3_POLICY_V2.get(t.get("family", ""), {"sat": True, "energy": True})
        rec = {"task_id": tid, "family": old.get("family"), "task_type": old.get("task_type"),
               "policy": pol, "timeout": False, "exec_ok": False, "n_errors": None,
               "sanity_ok": None, "verify_ok": None, "phys_ok": False, "sem_ok": False,
               "l3_sat_max_k": None, "l3_energy_pct": None, "note": ""}
        try:
            text = open(os.path.join(ws, rel), encoding="utf-8", errors="replace").read()
            rec["l1_static"] = (R.validate_i(text) or "").splitlines()[0][:60]
            msg = R.run_relap5(rel, timeout=600)
            if "运行超时" in msg:
                rec["timeout"] = True
                rec["note"] = "timeout"
            else:
                rec["exec_ok"] = "正常结束=True" in msg
                m = re.search(r"输出=(\S+)", msg)
                if rec["exec_ok"] and m:
                    o = m.group(1)
                    otxt = R._read_o(R._SB.resolve(o))
                    perr = R.parse_output(o)
                    mm = re.search(r"错误数=(\d+)", perr)
                    rec["n_errors"] = int(mm.group(1)) if mm else None
                    san = R.check_sanity(o)
                    rec["sanity_ok"] = R.sanity_passes(san)   # 统一判据（原写法检查了从不输出的“未通过”且误把[警告]当失败）
                    prm = t.get("params") or {}
                    va = assess(o, power=prm.get("power"), mdot=prm.get("mdot"),
                                sat=pol["sat"], energy=pol["energy"])
                    rec["l3_sat_max_k"] = va["sat_max_margin"]
                    rec["l3_energy_pct"] = va["energy_rel_pct"]
                    rec["l3_doubt"] = va["n_doubt"]
                    rec["verify_ok"] = (va["n_doubt"] == 0)
                    rec["phys_ok"] = bool(rec["sanity_ok"] and rec["verify_ok"])
                    sc = scalars(otxt, t.get("key_outputs") or [])
                    rec["sem_ok"] = compare(sc, old.get("expected") or {},
                                            t.get("key_outputs") or [])
        except Exception as e:  # noqa: BLE001
            rec["note"] = "异常: %s" % e
        rec["old_phys_ok"] = old.get("phys_ok")
        rec["old_sem_ok"] = old.get("sem_ok")
        f.write(json.dumps(rec, ensure_ascii=False) + "\n")
        f.flush()
        flag = "" if rec["phys_ok"] == rec["old_phys_ok"] else "  <== 改变"
        print("w%d [%d/%d] %-24s exec=%s phys %s->%s sem %s->%s (%.0fs)%s"
              % (k, j, len(todo), tid, rec["exec_ok"], rec["old_phys_ok"], rec["phys_ok"],
                 rec["old_sem_ok"], rec["sem_ok"], time.time() - t0, flag), flush=True)
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
        pf = open(os.path.join(HERE, "l3v2_w%d.log" % k), "w", encoding="utf-8")
        cmd = [sys.executable, os.path.abspath(__file__),
               "--shard", str(k), "--nshards", str(a.nshards)]
        procs.append((k, subprocess.Popen(cmd, stdout=pf, stderr=subprocess.STDOUT), pf))
    print("已启动 %d 个分片" % a.nshards)
    for k, p, pf in procs:
        p.wait()
        pf.close()
        print("分片 %d 结束 rc=%s" % (k, p.returncode))


if __name__ == "__main__":
    main()
