# -*- coding: utf-8 -*-
r"""基线 B1：**单次生成**（无工具、无闭环、无校验）。

分层抽样（每族最多 --per-family 道）→ 一次 LLM 调用直接产出输入卡 →
用**与主实验完全相同**的 L1–L4 评判 → 记录。

用法： python bench/baseline.py --per-family 4 --workers 6
产出： bench/baseline_results.jsonl
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import glob
import json
import os
import re
import sys
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ROOT)
sys.path.insert(0, HERE)

import registry  # noqa: E402
import tools.relap5 as R  # noqa: E402
from bench.agg import compare, scalars  # noqa: E402
from config import load  # noqa: E402
from llm import LLM, LLMError  # noqa: E402

OUT = os.path.join(HERE, "baseline_results.jsonl")
SYSPROMPT = ("你是一名 RELAP5 输入卡建模专家。请仅根据用户需求，直接给出**完整、可直接运行**的 "
             "RELAP5 输入卡；不要解释、不要省略。把全部卡行放进一个 ``` 代码块中。")


def extract_deck(text: str) -> str:
    """取**最大的代码块**（容忍无闭合栅栏），并去掉残留的栅栏行。"""
    t = text or ""
    blocks = re.findall(r"```[^\n]*\n(.*?)(?:```|\Z)", t, re.S)
    cand = max(blocks, key=len) if blocks else t
    lines = [ln for ln in cand.splitlines() if not ln.strip().startswith("```")]
    return "\n".join(lines).strip() + "\n"


def prompt_for(t: dict, examples: str = "") -> str:
    body = t["nl"]
    if t.get("context_deck"):
        body = (f"现有输入卡如下（文件 {t.get('context_name')}）：\n```\n{t['context_deck']}\n```\n\n"
                f"请按要求处理，并给出处理后的完整输入卡：{body}")
    return (examples + body) if examples else body


def one(llm: LLM, t: dict, exp: dict, examples: str = "", tag: str = "B1_single_shot",
        rep: int = 1) -> dict:
    msgs = [{"role": "system", "content": SYSPROMPT},
            {"role": "user", "content": prompt_for(t, examples)}]
    rec = {"task_id": t["task_id"], "family": t["family"], "task_type": t["task_type"],
           "baseline": tag, "repeat": rep, "exec_ok": False, "n_errors": None,
           "phys_ok": False, "sem_ok": False, "scalars": {},
           "expected": (exp or {}).get("scalars", {}), "tokens": 0, "iterations": 1}
    try:
        msg = llm.complete(msgs, tools=None)
    except LLMError as e:
        rec["err"] = f"LLMError: {e}"
        return rec
    rec["tokens"] = int((getattr(llm, "last_usage", {}) or {}).get("total_tokens") or 0)
    deck = extract_deck(msg.get("content") or "")
    if not deck.strip():
        rec["err"] = "空卡"
        return rec
    p = R._SB.resolve(f"base_{tag}_{t['task_id']}.i")
    try:
        p.write_text(deck, encoding="utf-8")
    except OSError:
        rec["err"] = "写卡失败"
        return rec
    rel = f"base_{tag}_{t['task_id']}.i"
    v = R.validate_i(deck)
    rec["l1_static"] = (v.splitlines()[0] if v else "")
    msg2 = R.run_relap5(rel, timeout=600)
    rec["exec_ok"] = "正常结束=True" in msg2
    m = re.search(r"输出=(\S+)", msg2)
    if not (rec["exec_ok"] and m):
        rec["n_errors"] = -1
        return rec
    o = m.group(1)
    try:
        otxt = R._read_o(R._SB.resolve(o))
        perr = R.parse_output(o)
        mm = re.search(r"错误数=(\d+)", perr)
        rec["n_errors"] = int(mm.group(1)) if mm else None
        san = R.check_sanity(o)
        rec["phys_ok"] = R.sanity_passes(san)      # 统一判据，见 tools/relap5.py:sanity_passes
        rec["scalars"] = scalars(otxt, t.get("key_outputs") or [])
        rec["sem_ok"] = compare(rec["scalars"], rec["expected"], t.get("key_outputs") or [])
    except Exception as e:  # noqa: BLE001
        rec["err"] = str(e)[:200]
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--per-family", type=int, default=4)
    ap.add_argument("--workers", type=int, default=6)
    ap.add_argument("--families", default="", help="逗号分隔，仅跑这些族")
    ap.add_argument("--fewshot", action="store_true", help="B2：给 2 个示例卡（仍无工具/无闭环/无校验）")
    ap.add_argument("--repeats", type=int, default=1,
                    help="重复轮次：同一批题跑 N 次，记录 repeat 字段（用于给基线误差棒）")
    ap.add_argument("--start", type=int, default=0, help="题库起始下标（分批跑用）")
    ap.add_argument("--end", type=int, default=10 ** 9, help="题库结束下标（分批跑用）")
    ap.add_argument("--skip-done", action="store_true",
                    help="跳过该基线已有结果的题（断网/中断后补跑用）")
    a = ap.parse_args()

    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:  # noqa: BLE001
        pass
    registry.load_plugins("tools")
    s = load()
    llm = LLM(s)
    tasks = [json.loads(l) for l in open(os.path.join(HERE, "tasks.jsonl"), encoding="utf-8")]
    exp = {}
    for line in open(os.path.join(HERE, "expected.jsonl"), encoding="utf-8"):
        try:
            r = json.loads(line)
            exp[r["task_id"]] = r
        except Exception:  # noqa: BLE001
            pass

    fams = set(x for x in a.families.split(",") if x)
    _done = set()
    if a.skip_done:
        _want = "B2_fewshot" if a.fewshot else "B1_single_shot"
        for line in open(OUT, encoding="utf-8", errors="replace"):
            try:
                _r = json.loads(line)
            except Exception:
                continue
            if _r.get("baseline") == _want and _r.get("repeat", 1) <= max(1, a.repeats):
                _done.add(_r["task_id"])
    byfam = {}
    for i, t in enumerate(tasks):
        if a.start <= i < a.end and (not fams or t["family"] in fams) \
                and t["task_id"] not in _done:
            byfam.setdefault(t["family"], []).append(t)
    sel = []
    for fam in sorted(byfam):
        sel += byfam[fam][:a.per_family]
    tag = "B2_fewshot" if a.fewshot else "B1_single_shot"
    examples = ""
    if a.fewshot:
        parts = []
        # 示例卡：正常在知识库；若知识库已隔离，则从 holdout 取**同一份**。
        # （few-shot 示例是写在提示里的，属 B2 基线定义的一部分，不是库检索）
        for rel, tier in (("knowledge/learned/horiz_pipe_flow_in_press_out.i", "learned"),
                          ("knowledge/reference/agent/ref_small_valve_trpvlv.i", "reference_agent")):
            fp = os.path.join(ROOT, rel)
            if not os.path.isfile(fp):
                fp = os.path.join(HERE, "holdout", tier, os.path.basename(rel))
            if os.path.isfile(fp):
                parts.append("以下是可正常运行的输入卡示例：\n```\n" +
                             open(fp, encoding="utf-8").read().strip() + "\n```")
        examples = "\n\n".join(parts) + "\n\n请参考上述格式，回答下面的需求。\n\n"
    print(f"基线 {tag}：抽样 {len(sel)} 道 / {len(byfam)} 族；并发 {a.workers}"
          f"{'（含 %d 个示例）' % (examples.count('示例')) if examples else ''}", flush=True)

    fout = open(OUT, "a", encoding="utf-8")
    t0 = time.time()
    done = 0
    total = len(sel) * max(1, a.repeats)
    for rep in range(1, max(1, a.repeats) + 1):
        with cf.ThreadPoolExecutor(max_workers=a.workers) as pool:
            futs = {pool.submit(one, llm, t, exp.get(t["task_id"]), examples, tag, rep): t
                    for t in sel}
            for fu in cf.as_completed(futs):
                t = futs[fu]
                try:
                    rec = fu.result()
                except Exception as e:  # noqa: BLE001
                    rec = {"task_id": t["task_id"], "family": t["family"],
                           "task_type": t["task_type"], "baseline": tag, "repeat": rep,
                           "exec_ok": False, "phys_ok": False, "sem_ok": False, "err": str(e)[:200]}
                fout.write(json.dumps(rec, ensure_ascii=False) + "\n")
                fout.flush()
                done += 1
                print(f"[r{rep} {done}/{total}] {rec['task_id']:26s} exec={rec['exec_ok']} "
                      f"phys={rec.get('phys_ok')} sem={rec.get('sem_ok')} ({time.time()-t0:.0f}s)",
                      flush=True)
    fout.close()
    print(f"完成 {done} 道（{a.repeats} 轮），用时 {time.time()-t0:.0f}s -> {OUT}")


if __name__ == "__main__":
    main()
