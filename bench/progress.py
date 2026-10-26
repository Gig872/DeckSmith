# -*- coding: utf-8 -*-
"""进度采集与渲染（CLI 与实时窗口共用）。

本轮起支持**评测条件**（带库 on / 无库 off）：自动跟随"最近在写"的那批结果，
避免把两批混在一起算进度。

用法： python bench/progress.py            # 打印一次（自动识别条件）
      python bench/progress.py off        # 指定条件
      python bench/progresswin.py          # 打开实时窗口
"""
from __future__ import annotations

import glob
import io
import json
import os
import re
import time
from collections import Counter, defaultdict

HERE = os.path.dirname(os.path.abspath(__file__))
TASKS = os.path.join(HERE, "tasks.jsonl")
EXPECTED = os.path.join(HERE, "expected.jsonl")

DEFAULT_SEC = {
    "single_pipe_steady": 30, "critical_nozzle": 10, "parallel_channels": 10,
    "jetmixer": 10, "mtpljun": 10, "separator": 15,
    "chf_dryout": 30, "pump_loop": 30, "valve_transient": 30, "accumulator": 30,
    "numerical_grid": 30, "numerical_dt": 60,
    "hs_gap": 40, "point_kinetics": 40, "turbine": 40, "modify_model": 40, "fix_deck": 40,
    "sbloca_blowdown": 60, "lof_transient": 90,
}


def load(path):
    out = []
    if os.path.isfile(path):
        for line in io.open(path, encoding="utf-8", errors="replace"):
            try:
                out.append(json.loads(line))
            except Exception:  # noqa: BLE001
                pass
    return out


def _result_files(cond=None, tag=None):
    """按**条件 + 批次标签**精确取文件，避免 A / κ / 探针 混在一起。"""
    if cond and tag is not None:
        base = f"run_results_k{cond}{tag}"
        pats = [base + ".jsonl", base + "_w*.jsonl"]
    elif cond:
        pats = [f"run_results_k{cond}*.jsonl"]
    else:
        pats = ["run_results*.jsonl"]
    out = []
    for pat in pats:
        out += glob.glob(os.path.join(HERE, pat))
    return sorted(set(out))


def _parse_name(b: str):
    """从结果文件名解析 (cond, tag)。run_results_kon_half_w3 -> ('on','_half')"""
    stem = b[:-6] if b.endswith(".jsonl") else b
    stem = re.sub(r"_w\d+$", "", stem)
    m = re.match(r"run_results_k(on|off)(.*)$", stem)
    if not m:
        return None, ""
    return m.group(1), m.group(2)


def current_batch():
    """取**最近被写入**的结果文件所属批次。返回 (batch, age, tag)。
    batch ∈ {'on','off','baseline'}；tag 如 ''/'_kappa'/'_half'/'_oral'。
    进度窗口据此跟随"当前真正在跑的批次"，而不是停在最后一个完成的条件上。"""
    cands = _result_files() + sorted(glob.glob(os.path.join(HERE, "baseline_results*.jsonl")))
    if not cands:
        return None, None, ""
    p = max(cands, key=os.path.getmtime)
    age = time.time() - os.path.getmtime(p)
    b = os.path.basename(p)
    if b.startswith("baseline"):
        return "baseline", age, ""
    cond, tag = _parse_name(b)
    return cond, age, tag


def current_condition():
    """**最后一次主实验**的条件（只看无标签的主实验文件，不看探针/κ/基线）。"""
    files = _result_files("on", "") + _result_files("off", "")
    for p in sorted(files, key=os.path.getmtime, reverse=True):
        for r in reversed(load(p)):
            k = str(r.get("knowledge") or "")
            if k in ("on", "off"):
                return k
    return None


def load_results(cond=None, tag=None):
    rows = []
    for p in _result_files(cond, tag):
        rows.extend(load(p))
    if cond:
        rows = [r for r in rows if str(r.get("knowledge") or "") == cond]
    return rows


def bar(frac: float, width: int = 40, fill: str = "#", empty: str = "-") -> str:
    n = max(0, min(width, int(round(frac * width))))
    return "[" + fill * n + empty * (width - n) + "]"


def baseline_progress() -> dict:
    """基线各变体的完成题数（去重后）。"""
    rows = []
    for p in sorted(glob.glob(os.path.join(HERE, "baseline_results*.jsonl"))):
        rows.extend(load(p))
    last = {}
    for r in rows:
        last[(r["task_id"], r.get("baseline"))] = r
    return dict(Counter(k[1] for k in last))


def collect(cond=None, tag=None) -> dict:
    batch, age, cur_tag = current_batch()
    if tag is None:
        tag = cur_tag if batch in ("on", "off") else ""
    if cond is None and batch in ("on", "off"):
        cond = batch
    if cond is None:
        cond = current_condition()      # 批次不是主实验时，回退到"最后一次主实验"
    tasks = load(TASKS)
    valid_ids = {r["task_id"] for r in load(EXPECTED) if r.get("valid")}
    res = load_results(cond, tag)
    done = [r["task_id"] for r in res]
    total, n = len(tasks), len(done)

    # 只统计本轮（当前条件）的日志
    logpat = f"*k{cond}*.log" if cond else "*.log"
    logs = sorted(glob.glob(os.path.join(HERE, logpat)))
    obs, elapsed, best_last = defaultdict(list), None, -1.0
    for lg in logs:
        if not os.path.isfile(lg):
            continue
        prev, last = 0.0, 0.0
        for ln in io.open(lg, encoding="utf-8", errors="replace"):
            m = re.match(r"(?:r\d+|w\S+)\s+\[(\d+)\] (\S+).*?\((\d+)s\)", ln)
            if not m:
                continue
            cum = float(m.group(3))
            obs[m.group(2).rsplit("_", 1)[0]].append(max(cum - prev, 0.0))
            prev = last = cum
        if last > best_last:
            best_last, elapsed = last, last

    tot_fam = Counter(t["family"] for t in tasks)
    done_fam = Counter(r["family"] for r in res)
    eta_s = 0.0
    fam_rows = []
    for fam in sorted(tot_fam):
        tt, d = tot_fam[fam], done_fam.get(fam, 0)
        per = (sum(obs[fam]) / len(obs[fam])) if obs.get(fam) else DEFAULT_SEC.get(fam, 40.0)
        eta_s += max(tt - d, 0) * per
        fam_rows.append((fam, d, tt, per))
    nworkers = max(1, len([p for p in _result_files(cond, tag)
                           if "_w" in os.path.basename(p)]))
    eta_s /= nworkers

    c = Counter()
    try:
        from metrics import load_key_outputs, _cmp
        exps = {r["task_id"]: r for r in load(EXPECTED)}
        ko = load_key_outputs()
        for r in res:
            e = (exps.get(r["task_id"]) or {}).get("scalars", {})
            r["sem_ok"] = _cmp(r.get("scalars") or {}, e, ko.get(r["task_id"], []))
    except Exception:  # noqa: BLE001
        pass
    n_to = n_cr = n_of = n_ofok = 0
    for r in res:
        c["exec"] += bool(r.get("exec_ok"))
        c["phys"] += bool(r.get("exec_ok") and r.get("phys_ok"))
        c["sem"] += bool(r.get("sem_ok"))
        n_to += bool(r.get("timeout"))
        n_cr += bool(r.get("crashed"))
        if r.get("exec_ok_first") is not None:
            n_of += 1
            n_ofok += bool(r["exec_ok_first"])
    toks = [r.get("tokens") or 0 for r in res]
    tok_sum = sum(toks)
    tok_avg = (tok_sum / n) if n else 0
    tok_eta = tok_avg * max(float(total - n), 0)

    # 顶部进度条应跟随**当前批次**，而不是固定跟随主实验
    bp = baseline_progress()
    if batch == "baseline":
        _vals = list(bp.values())
        bar_done = min(_vals) if _vals else 0      # 取最不完整的变体 = 正在跑的
        bar_total = total
        bar_label = "基线"
    else:
        _cn = {"on": "带库", "off": "无库"}.get(cond, "(未识别)")
        bar_done, bar_total, bar_label = n, total, _cn

    return {"cond": cond, "tag": tag, "batch": batch, "age": age, "baseline": bp,
            "bar_done": bar_done, "bar_total": bar_total, "bar_label": bar_label,
            "total": total, "n": n, "frac": (bar_done / bar_total if bar_total else 0.0),
            "elapsed": elapsed, "eta_s": eta_s, "workers": nworkers, "fam_rows": fam_rows,
            "exec": c["exec"], "phys": c["phys"], "sem": c["sem"],
            "timeout": n_to, "crashed": n_cr, "first_n": n_of, "first_ok": n_ofok,
            "last": (res[-1] if res else None),
            "tok_sum": tok_sum, "tok_avg": tok_avg, "tok_eta": tok_eta,
            "valid_done": len(set(done) & valid_ids), "valid_total": len(valid_ids)}


def render_text(d: dict) -> str:
    L = []
    cond = d.get("cond")
    cname = {"on": "带库", "off": "无库"}.get(cond, "(未识别)")
    batch = d.get("batch")
    age = d.get("age")
    bname = {"on": "主实验·带库", "off": "主实验·无库",
             "baseline": "基线 B1/B2"}.get(batch, "(无活动批次)")
    if d.get("tag"):
        bname += d["tag"]
    tag = "进行中" if (age is not None and age < 180) else (
        f"已停止（{int(age/60)} 分钟前）" if age is not None else "—")
    L.append(f"当前批次 {bname} · {tag}")
    if batch == "baseline":
        bp = d.get("baseline") or {}
        L.append("  基线进度：" + " ｜ ".join(
            f"{k} {v}/329" for k, v in sorted(bp.items())) or "  (尚无)")
    last_main = batch not in ("on", "off")
    L.append(f"主实验·{cname}（knowledge={cond}）"
             + ("  ← 上次批次，非当前" if last_main else ""))
    L.append(f"{d.get('bar_label','总进度')}进度 {bar(d['frac'])} "
             f"{d.get('bar_done',d['n'])}/{d.get('bar_total',d['total'])}  {d['frac']*100:5.1f}%")
    el = d["elapsed"] or 0
    rate = (el / d["n"]) if d["n"] else 0
    L.append(f"已用 {el/60:.1f} min ｜ 已完成族平均 {rate:.0f} s/题 ｜ "
             f"并发 {d.get('workers',1)} × ｜ 预计剩余 {d['eta_s']/60:.0f} min")
    n = d["n"] or 0
    L.append(f"判定：exec {d['exec']}/{n} ｜ phys {d['phys']}/{n} ｜ sem {d['sem']}/{n}")
    L.append(f"首跑可运行 {d['first_ok']}/{d['first_n']} ｜ 超时 {d['timeout']} ｜ "
             f"崩溃 {d['crashed']}")
    L.append(f"token：累计 {d['tok_sum']/1e6:.2f} M ｜ 均 {d['tok_avg']/1e3:.0f} k/题 ｜ "
             f"预计还需 {d['tok_eta']/1e6:.0f} M")
    if d["last"]:
        r = d["last"]
        L.append(f"最近完成：{r['task_id']}  exec={r['exec_ok']} phys={r['phys_ok']} "
                 f"sem={r['sem_ok']}")
    L.append("")
    L.append("分族进度：")
    for fam, dd, tt, per in d["fam_rows"]:
        L.append(f"  {fam:22s} {bar(dd/tt, 18)} {dd:3d}/{tt:3d}  ~{per:.0f}s/题")
    L.append("")
    L.append(f"（有效题已完成 {d['valid_done']}/{d['valid_total']}；最终指标只统计有效题）")
    return "\n".join(L)


def main():
    import sys
    cond = sys.argv[1] if len(sys.argv) > 1 else None
    print(render_text(collect(cond)))


if __name__ == "__main__":
    main()
