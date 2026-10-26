# -*- coding: utf-8 -*-
"""runner：逐题调用 LLM 智能体，跑通后施加 L1–L4 判定，并记录结果。

用法：
  python bench/runner.py --start 0 --end 5 --repeats 1     # 小样本试跑
  python bench/runner.py --repeats 3                        # 全量（花钱）

产出 bench/run_results.jsonl，每行：
  {task_id, family, task_type, repeat, exec_ok, n_errors, phys_ok, sem_ok,
   scalars, expected, iterations, tokens}
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time

# 控制台/重定向的编码兜底：Windows 默认 GBK，日志里的 ⚠ 等符号会抛
# UnicodeEncodeError，且恰好发生在"欠费截断"这类错误分支上，会把真正的
# 原因盖成编码错误。统一按 UTF-8 输出，无法编码的字符替成 ?。
try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")
except Exception:  # noqa: BLE001
    pass

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 评测隔离：workspace 与 learned 库须在 import config / 工具之前设定，
# 否则知识库与工作目录会被固定成默认值（污染源无法隔离）。
_WS = os.environ.get("AGENT_WORKSPACE") or os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "workspace", "serial")
os.environ.setdefault("AGENT_WORKSPACE", _WS)
os.environ.setdefault("AGENT_LEARNED_DIR", os.path.join(_WS, "learned"))

# 评测条件（带库/无库）——须在 import config / tools 之前装配
from bench.evalenv import setup as _setup_eval, mode_from_argv as _kmode  # noqa: E402
KNOWLEDGE = _setup_eval(_kmode(sys.argv))

import registry  # noqa: E402
import tools.relap5 as R  # noqa: E402
from bench.harness import evaluate, prepare, set_knowledge, set_tag  # noqa: E402
from config import load  # noqa: E402
from llm import OutOfCredit  # noqa: E402
from bench.crashguard import (mark_out_of_credit, clear_mark, is_out_of_credit,  # noqa: E402
                              acquire_lock, release_lock)

set_knowledge(KNOWLEDGE)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT_OUTER = os.path.dirname(HERE)
TASKS = os.path.join(HERE, "tasks.jsonl")
EXPECTED = os.path.join(HERE, "expected.jsonl")
OUT = os.path.join(HERE, "run_results.jsonl")


def load_expected() -> dict:
    exp = {}
    if os.path.isfile(EXPECTED):
        for line in open(EXPECTED, encoding="utf-8"):
            try:
                r = json.loads(line)
                exp[r["task_id"]] = r
            except Exception:  # noqa: BLE001
                pass
    return exp


def one(s, t, exp, budget):
    """跑一次：委托 bench.harness.evaluate（与并发 worker 共用同一套单题逻辑）。"""
    return evaluate(s, t, exp, budget["repeat"])


def done_ids() -> set:
    """已完成的 task_id（含并发 worker 的 run_results_w*.jsonl）。"""
    ids = set()
    import glob
    for p in glob.glob(os.path.join(HERE, "run_results*.jsonl")):
        for line in open(p, encoding="utf-8"):
            try:
                ids.add(json.loads(line)["task_id"])
            except Exception:  # noqa: BLE001
                pass
    return ids


def done_ids_this_arm(tag: str, repeats: int) -> set:
    """**仅本臂**已完成的 (task_id, repeat)，用于欠费中断后续跑。

    为什么不能用 done_ids()：它扫全部 run_results*.jsonl，跨臂共用题集时会让
    Q 臂跳过 D 臂做过的题。续跑必须按 (标签, 重复轮次) 精确去重。
    """
    import glob
    key = set()
    pats = [os.path.join(HERE, f"run_results_k{KNOWLEDGE}{tag}.jsonl")]
    pats += glob.glob(os.path.join(HERE, f"run_results_k{KNOWLEDGE}{tag}_w*.jsonl"))
    for p in pats:
        if not os.path.isfile(p):
            continue
        for line in open(p, encoding="utf-8"):
            try:
                r = json.loads(line)
                key.add((r["task_id"], int(r.get("repeat") or 1)))
            except Exception:  # noqa: BLE001
                pass          # 进程被杀时最后一行可能截断，忽略即可
    return key


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=10**9)
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--families", default="", help="逗号分隔，仅跑这些族")
    ap.add_argument("--workers", type=int, default=1, help="并发进程数（>1 时每题独立工作目录）")
    ap.add_argument("--skip-done", action="store_true", help="跳过已有结果的题")
    ap.add_argument("--resume", action="store_true",
                    help="断点续跑：只跳过**本臂**输出文件里已完成的 (题目, 轮次)。"
                         "欠费中断后用同参数加本开关即可接着跑，且不会跨臂误跳。")
    ap.add_argument("--knowledge", choices=["on", "off", "off-strict"], default="off",
                    help="评测条件：on=带样例库，off=无库（历史口径），"
                         "off-strict=严格空库（每题清空、存与取同一目录）")
    ap.add_argument("--per-family", type=int, default=0,
                    help="每族仅取前 N 题（分层抽样；0=不限制）")
    ap.add_argument("--tag", default="",
                    help="输出文件名后缀（如 _kappa），避免与主实验结果撞名")
    ap.add_argument("--tasks", default="",
                    help="改用另一份题库文件（如语域探针的改写题面）")
    ap.add_argument("--only", default="",
                    help="逗号分隔的 task_id：**只跑这些**（用于精确补跑受损题，"
                         "避免 --skip-done 跨批次误跳）")
    a = ap.parse_args()
    set_tag(a.tag)

    # 批次互斥：同一 (条件, 标签) 只允许一个 runner，否则两组共用工作目录会互相清空产物卡
    _lk_tag = f"{KNOWLEDGE}{a.tag or ''}"
    _ok, _lpath, _opid = acquire_lock(HERE, _lk_tag)
    if not _ok:
        print(f"[拒绝] 已有同一批次在跑（tag={a.tag or '(主实验)'}, cond={KNOWLEDGE}, pid={_opid}）。\n"
              f"  同一标签的第二个 runner 会与第一个共用工作目录、互相删掉对方的产物卡，"
              f"导致评测找不到文件。已拒绝启动。", flush=True)
        return

    _tf = a.tasks or TASKS
    if a.tasks and not os.path.isabs(_tf):
        _tf = os.path.join(HERE, _tf)
    tasks = [json.loads(l) for l in open(_tf, encoding="utf-8")]
    fams = set(x for x in a.families.split(",") if x)
    seen = done_ids() if a.skip_done else set()
    only = set(x for x in a.only.split(",") if x.strip())
    sel = [i for i, t in enumerate(tasks)
           if a.start <= i < a.end and (not fams or t["family"] in fams)
           and (not only or t["task_id"] in only)
           and t["task_id"] not in seen]
    if a.per_family:
        from collections import defaultdict
        _cnt = defaultdict(int)
        _keep = []
        for i in sel:
            f = tasks[i]["family"]
            if _cnt[f] < a.per_family:
                _cnt[f] += 1
                _keep.append(i)
        sel = _keep
    print(f"选中 {len(sel)} 道；重复 {a.repeats} 次；并发 {a.workers}", flush=True)

    if a.workers > 1:
        import subprocess
        clear_mark(HERE)
        procs = []
        for w in range(a.workers):
            idxs = sel[w::a.workers]
            if not idxs:
                continue
            out = os.path.join(HERE, f"run_results_k{KNOWLEDGE}{a.tag}_w{w}.jsonl")
            log = open(os.path.join(HERE, f"_worker_k{KNOWLEDGE}{a.tag}_w{w}.log"),
                       "w", encoding="utf-8")
            _cmd = [sys.executable, os.path.join(HERE, "_worker.py"),
                    "--indices", ",".join(str(x) for x in idxs),
                    "--workspace", f"workspace_k{KNOWLEDGE}{a.tag}_w{w}", "--out", out,
                    "--repeats", str(a.repeats), "--knowledge", a.knowledge,
                    "--tag", a.tag, "--tasks", a.tasks or ""]
            if a.resume:
                _cmd.append("--resume")       # 各 worker 读自己的输出文件续跑
            p = subprocess.Popen(_cmd, cwd=ROOT_OUTER,
                                 stdout=log, stderr=subprocess.STDOUT)
            procs.append((w, len(idxs), p, log))
            print(f"  worker {w}: {len(idxs)} 道 (pid {p.pid})", flush=True)
        for w, n, p, log in procs:
            p.wait()
            log.close()
            print(f"worker {w} 结束 rc={p.returncode}", flush=True)
        if is_out_of_credit(HERE):
            print("⚠ 本批因【欠费】被截断——未完成部分不得记为失败，"
                  "分析时须剔除被截断的尾巴（bench/OUT_OF_CREDIT）", flush=True)
        print("并发完成 ->", os.path.join(HERE, "run_results_w*.jsonl"))
        release_lock(_lpath)
        return

    if a.skip_done:
        seen = done_ids()
    registry.load_plugins("tools")
    s = load()
    prepare(s.workspace)
    exp = load_expected()

    out_path = os.path.join(HERE, f"run_results_k{KNOWLEDGE}{a.tag}.jsonl")
    # 续跑：只认本臂输出文件里的 (task_id, repeat)，跨臂不互相影响
    done = done_ids_this_arm(a.tag, a.repeats) if a.resume else set()
    sel2 = [i for i in sel if tasks[i]["task_id"] not in seen]
    if done:
        print(f"续跑：本臂已完成 {len(done)} 条，跳过", flush=True)
    print(f"串行执行 {len(sel2)} 道；模型 {s.model or '(未配置)'}", flush=True)

    if not a.resume:
        clear_mark(HERE)                # 清掉上次的欠费标记（续跑时保留，便于追溯）
    fout = open(out_path, "a", encoding="utf-8")
    t0 = time.time()
    for rep in range(1, a.repeats + 1):
        for i in sel2:
            t = tasks[i]
            if (t["task_id"], rep) in done:
                continue
            try:
                rec = one(s, t, exp.get(t["task_id"]), {"repeat": rep})
            except OutOfCredit as e:
                mark_out_of_credit(HERE, s.model, str(e))
                print(f"⚠ 欠费截断：已在第 {i} 题停止（未完成部分不记为失败）", flush=True)
                print(f"  续跑命令：同参数追加 --resume", flush=True)
                fout.close()
                return
            fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
            fout.flush()
            print(f"r{rep} [{i}] {t['task_id']:24s} exec={rec['exec_ok']} "
                  f"phys={rec['phys_ok']} sem={rec['sem_ok']} ({time.time()-t0:.0f}s)",
                  flush=True)
    fout.close()
    release_lock(_lpath)
    print(f"完成，用时 {time.time()-t0:.0f}s -> {out_path}")


if __name__ == "__main__":
    main()
