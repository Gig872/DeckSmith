# -*- coding: utf-8 -*-
"""L2 判据"真做"：分类型终止判据 + 参考解标定 + 全量重判（零 LLM token）。

判据（不改 tools/relap5.py 的任何既有函数，只读复用 _normal_end / steady_declared）：

结构（两族共有）
  * 输入处理通过：输出含 `input processing completed successfully`，且不含
    `errors detected during input processing`；
  * 正常结束：复用 tools.relap5._normal_end（含正常三结束语，显式排除
    `terminated by failure`）；
  * 无致命错误：`.o` 中不含任意 `********` 错误行（逐行全量统计，不用
    _errors(t, n=8) 的截断结果）；
  * 无发散：无 `terminated by failure`；所有状态快照中压力 > 0；无物性失败标记。

稳态族（STEADY，与 bench/calib_l2l3a.py 同一集合）
  * 取 .o 中最后两个不同编辑时刻的状态快照；
  * 关键量：逐控制体 pressure / tempf / tempg，以及系统总质量 mass；
  * 相对变化 rel = |b-a| / max(|a|, |b|, floor)，取全量最大；
  * max_rel <= 0.01（默认）判收敛。

瞬态族（其余所有族）
  * 从输入卡 201 卡取 t_end；
  * 输出 `Final time` 达到 t_end（容差 max(0.5%*t_end, 0.05 s)）；
  * 且不发散（同上）。

运行隔离：每个 worker 独立工作目录（复制 tpf* 物性文件），串行使用；
.o 体积 > 300 MB 立即杀进程。

用法（本模块既可 import，也可直接跑）：
  python bench/l2_conv.py calib  --workers 8 --outdir ...
  python bench/l2_conv.py rejudge --workers 8 --outdir ...
"""
from __future__ import annotations

import argparse
import glob
import json
import multiprocessing as mp
import os
import re
import shutil
import subprocess
import sys
import time

ROOT = r"C:\relap-5\agent-kit"
BENCH = os.path.join(ROOT, "bench")
RELAP5_DIR = r"C:\relap-5\relap5程序"
RELAP5_EXE = os.path.join(RELAP5_DIR, "relap5.exe")
DEFAULT_OUT = r"C:\relap-5\论文\数据\20_L2真做"
MAX_O_BYTES = 300 * 1024 * 1024
sys.path.insert(0, ROOT)
os.environ.setdefault("AGENT_WORKSPACE", os.path.join(ROOT, "workspace_l2conv"))

# 稳态族集合：直接复用 bench/calib_l2l3a.py 的定义（论文口径）
STEADY = {"single_pipe_steady", "hs_gap", "chf_dryout", "point_kinetics", "parallel_channels",
          "pump_loop", "turbine", "separator", "mtpljun", "jetmixer", "critical_nozzle",
          "numerical_grid"}

# ---- 与 tools/relap5.py 的只读复用 ----
try:
    import tools.relap5 as _R
    _normal_end = _R._normal_end
    steady_declared = _R.steady_declared
except Exception:  # noqa: BLE001  (standalone fallback，语义逐字一致)
    def _normal_end(t: str) -> bool:
        tail = (t or "")[-3000:]
        if "terminated by failure" in tail.lower():
            return False
        return ("Transient terminated" in tail
                or "input processing completed successfully" in tail.lower()
                or "has reached steady state" in tail)

    def steady_declared(t: str) -> bool:
        return "has reached steady state" in (t or "")[-3000:]

_HDR_STATE = re.compile(r"^\s*\d?\s*Vol\.no\..*pressure.*temp(f|g)?.*$")
_ANY_VOLNO = re.compile(r"^\s*\d?\s*Vol\.no\.")
_ROWV = re.compile(r"^\s*(-?\d{3}-\d{6})\s+(.*)$")
_TIME = re.compile(r"time=\s*([\d.Ee+-]+)")
_MASS = re.compile(r"mass\s*=\s*([\d.Ee+-]+)\s*kg\s+mass error=\s*([\d.Ee+-]+)")
_FINAL = re.compile(r"Final time=\s*([\d.Ee+-]+)")
_CARD201 = re.compile(r"^\s*201\s+([\d.Ee+-]+)")
_PROPFAIL = re.compile(
    r"(property\s+(error|failure)|properties?\s+(failed|out of range)|"
    r"thermodynamic\s+(error|failure)|property\s+table\s+error)", re.I)
_CTRL = {" ", "0", "1", "+"}


def clean_output(raw: str) -> str:
    """与 tools/relap5.py:_clean 完全一致的读入清洗：去掉 RELAP5 每行首列控制字符。

    不清洗会让表头（首字符 0）比数据行（首字符空格）多一列，导致列错位。
    """
    out = []
    for line in (raw or "").split("\n"):
        if line and line[0] in _CTRL:
            out.append(line[1:].rstrip("\r"))
        else:
            out.append(line.rstrip("\r"))
    return "\n".join(out)


# ------------------------------------------------------------------ static parse
def parse_t_end(deck_text: str):
    """从输入卡 201（时间步控制）取 t_end（卡内第 2 列）。"""
    for line in (deck_text or "").splitlines():
        m = _CARD201.match(line)
        if m:
            try:
                return float(m.group(1))
            except ValueError:
                pass
    return None


def parse_final_time(text: str):
    ms = _FINAL.findall(text or "")
    return float(ms[-1]) if ms else None


def parse_snapshots(text: str):
    """抽取各编辑时刻的状态快照。

    返回 [(time, table, mass)]，按 time 升序；table = {volid: {col: float}}。
    同一时刻若有多张表（输入处理表 + 瞬态表），保留最后一张。
    """
    lines = (text or "").split("\n")
    cur = None
    by_t, mass_t = {}, {}
    i = 0
    while i < len(lines):
        ln = lines[i]
        tm = _TIME.search(ln)
        if tm:
            try:
                cur = float(tm.group(1))
            except ValueError:
                pass
        mm = _MASS.search(ln)
        if mm and cur is not None:
            try:
                mass_t[cur] = float(mm.group(1))
            except ValueError:
                pass
        if _HDR_STATE.match(ln):
            names = ln.split()
            idx = {k: (names.index(k) if k in names else None)
                   for k in ("pressure", "tempf", "tempg", "voidg")}
            table = {}
            j = i + 1
            while j < len(lines) and not _ANY_VOLNO.match(lines[j]):
                rm = _ROWV.match(lines[j])
                if rm:
                    tk = lines[j].split()
                    try:
                        vid = tk[0]
                        rec = {}
                        for k, pos in idx.items():
                            if pos is not None:
                                rec[k] = float(tk[pos])
                        table[vid] = rec
                    except (ValueError, IndexError):
                        pass
                j += 1
            if table and cur is not None:
                by_t[cur] = table          # 同一时刻后来者覆盖
            i = j
            continue
        i += 1
    return [(t, by_t[t], mass_t.get(t)) for t in sorted(by_t)]


# ------------------------------------------------------------------ criteria
def _rel(a, b, floor=1e-12):
    return abs(b - a) / max(abs(a), abs(b), floor)


def steady_window_metric(snaps, k=4):
    """有界振荡的收敛判据（仅在"最后两快照"不过时启用）。

    对最后 k 个快照：比较前 k/2 个与后 k/2 个的**均值**（相对变化 <= rel_tol），
    并要求整段峰峰相对幅度 <= 10%（有界）。用于区分"稳定的极限环"与
    "单调漂移/发散"：前者两窗均值几乎不变，后者两窗均值显著不同。
    返回 (mean_metric, amp_metric, where, detail)。
    """
    if len(snaps) < k or k % 2:
        return None, None, "", "insufficient snapshots"
    ss = snaps[-k:]
    half = k // 2
    keys = None
    for _t, tab, _m in ss:
        ks = {(vid, col) for vid, rec in tab.items()
              for col in ("pressure", "tempf", "tempg") if col in rec}
        keys = ks if keys is None else (keys & ks)
    keys = sorted(keys or [])
    worst_mean, worst_amp, where = 0.0, 0.0, ""
    for vid, col in keys:
        vals = [s[1][vid][col] for s in ss]
        if col.startswith("temp"):
            if not all(0.0 < v <= 6000.0 for v in vals):
                continue
        m_a = sum(vals[:half]) / half
        m_b = sum(vals[half:]) / half
        r_mean = _rel(m_a, m_b)
        scale = max(max(abs(v) for v in vals), 1e-12)
        r_amp = (max(vals) - min(vals)) / scale
        if r_mean > worst_mean:
            worst_mean, where = r_mean, f"{vid}.{col}"
        worst_amp = max(worst_amp, r_amp)
    masses = [s[2] for s in ss]
    if all(m is not None for m in masses):
        m_a = sum(masses[:half]) / half
        m_b = sum(masses[half:]) / half
        r_mean = _rel(m_a, m_b)
        r_amp = (max(masses) - min(masses)) / max(max(abs(m) for m in masses), 1e-12)
        if r_mean > worst_mean:
            worst_mean, where = r_mean, "system.mass"
        worst_amp = max(worst_amp, r_amp)
    detail = (f"window{k}: mean_rel={worst_mean:.5g} @{where or '-'} "
              f"amp={worst_amp:.5g}")
    return worst_mean, worst_amp, where, detail


def steady_metric(prev, cur):
    """最后两快照的最大相对变化。返回 (metric, detail)。

    涵盖逐控制体 pressure/tempf/tempg 与系统总质量。
    温度哨兵值（<=0 或 >6000 K）不参与（RELAP5 对空相填 0）；压力全部参与。
    """
    t_prev, tab_prev, m_prev = prev
    t_cur, tab_cur, m_cur = cur
    worst, where = 0.0, ""
    for vid in sorted(set(tab_prev) & set(tab_cur)):
        for col in ("pressure", "tempf", "tempg"):
            a, b = tab_prev[vid].get(col), tab_cur[vid].get(col)
            if a is None or b is None:
                continue
            if col.startswith("temp") and not (0.0 < b <= 6000.0 and 0.0 < a <= 6000.0):
                continue
            r = _rel(a, b)
            if r > worst:
                worst, where = r, f"{vid}.{col}"
    mass_note = ""
    if m_prev is not None and m_cur is not None:
        r = _rel(m_prev, m_cur)
        mass_note = f" mass={m_prev:.6g}->{m_cur:.6g} rel={r:.3g}"
        if r > worst:
            worst, where = r, "system.mass"
    detail = f"dt={t_cur - t_prev:.6g}s worst={where or '-'}={worst:.5g}{mass_note}"
    return worst, detail


def evaluate_text(text: str, deck_text: str, family: str,
                  rel_tol: float = 0.01, time_tol_frac: float = 0.005,
                  time_tol_abs: float = 0.05, amp_tol: float = 0.10,
                  window_k: int = 6) -> dict:
    """对一次 .o 施加新 L2。返回 {exec_ok_new, reason, final_time, converged_metric, detail}。"""
    text = clean_output(text or "")
    low = text.lower()
    final_time = parse_final_time(text)
    snaps = parse_snapshots(text)
    res = {"exec_ok_new": False, "reason": "", "final_time": final_time,
           "converged_metric": None, "detail": "",
           "strict_metric": None, "window_metric": None, "window_amp": None,
           "conv_mode": "", "input_ok": False, "normal_end": bool(_normal_end(text)),
           "t_end": None}

    # 1) 结构：输入处理
    if "errors detected during input processing" in low:
        res["reason"] = "input_processing_failed"
        return res
    if "input processing completed successfully" not in low:
        res["reason"] = "input_processing_not_completed"
        return res
    res["input_ok"] = True

    # 2) 结构：正常结束（复用既有判据；已排除 terminated by failure）
    if not _normal_end(text):
        res["reason"] = "not_normal_end"
        return res

    # 3) 发散 / 致命错误（全量，不用 _errors 的 n=8 截断）
    n_star = sum(1 for ln in (text or "").split("\n") if "********" in ln)
    if n_star:
        res["reason"] = "fatal_error_lines"
        res["detail"] = f"******** lines={n_star}"
        return res
    if "terminated by failure" in low:
        res["reason"] = "terminated_by_failure"
        return res
    if _PROPFAIL.search(text or ""):
        res["reason"] = "property_failure"
        return res
    for tt, tab, _m in snaps:
        for vid, rec in tab.items():
            p = rec.get("pressure")
            if p is not None and p <= 0:
                res["reason"] = "nonpositive_pressure"
                res["detail"] = f"time={tt:g} {vid} p={p:g}"
                return res

    # 4) 分族终止判据
    if family in STEADY:
        if len(snaps) < 2:
            # RELAP5 自判稳态但只写了一帧时，接受（无两帧可算，metric 记 None）
            if steady_declared(text):
                res["exec_ok_new"] = True
                res["reason"] = "ok_steady_declared"
                return res
            res["reason"] = "insufficient_snapshots"
            res["detail"] = f"snapshots={len(snaps)}"
            return res
        metric, detail = steady_metric(snaps[-2], snaps[-1])
        # 次判据（有界振荡）的指标总是计算并落盘，供阈值敏感性离线复用。
        w_mean, w_amp, _w, w_detail = steady_window_metric(snaps, k=window_k)
        res["converged_metric"] = metric
        res["strict_metric"] = metric
        res["window_metric"] = w_mean
        res["window_amp"] = w_amp
        res["detail"] = detail + " | " + w_detail
        if metric <= rel_tol:
            res["exec_ok_new"] = True
            res["reason"] = "ok_converged"
            res["conv_mode"] = "last2"
            return res
        # 次判据：有界振荡（两窗均值稳定 + 幅度有界）。阈值不放松，只改快照口径。
        if (w_mean is not None and w_mean <= rel_tol
                and w_amp is not None and w_amp <= amp_tol):
            res["exec_ok_new"] = True
            res["reason"] = "ok_converged_window"
            res["conv_mode"] = f"window{window_k}"
        else:
            res["reason"] = "not_converged"
        return res

    # 瞬态族：跑到 t_end 且不发散
    t_end = parse_t_end(deck_text)
    res["t_end"] = t_end
    if t_end is None:
        res["reason"] = "no_t_end"
        return res
    if final_time is None:
        res["reason"] = "no_final_time"
        return res
    tol = max(time_tol_frac * abs(t_end), time_tol_abs)
    res["converged_metric"] = final_time / t_end if t_end else None
    res["detail"] = f"final/t_end={final_time:g}/{t_end:g} tol={tol:g}"
    if final_time + tol >= t_end:
        res["exec_ok_new"] = True
        res["reason"] = "ok_endpoint"
    else:
        res["reason"] = "endpoint_not_reached"
    return res


# ------------------------------------------------------------------ runner
def _prepare_worker_dir(workdir: str):
    os.makedirs(workdir, exist_ok=True)
    for f in os.listdir(RELAP5_DIR):
        if f.lower().startswith("tpf"):
            dst = os.path.join(workdir, f)
            if not os.path.exists(dst):
                try:
                    shutil.copy2(os.path.join(RELAP5_DIR, f), dst)
                except OSError:
                    pass


def run_deck(deck_text: str, workdir: str, timeout: float = 900.0) -> dict:
    """在独立目录跑一张卡。返回 {status, text, o_bytes, elapsed}。"""
    _prepare_worker_dir(workdir)
    ip = os.path.join(workdir, "case.i")
    op = os.path.join(workdir, "case.o")
    rp = os.path.join(workdir, "case.r")
    with open(ip, "w", encoding="utf-8", errors="replace") as f:
        f.write(deck_text or "")
    for p in (op, rp, os.path.join(workdir, "rstplt"),
              os.path.join(workdir, "plotfl"), os.path.join(workdir, "stripf")):
        try:
            os.remove(p)
        except OSError:
            pass
    t0 = time.time()
    try:
        proc = subprocess.Popen([RELAP5_EXE, "-i", ip, "-o", op, "-r", rp],
                                cwd=workdir, stdout=subprocess.DEVNULL,
                                stderr=subprocess.STDOUT)
    except Exception as e:  # noqa: BLE001
        return {"status": "run_failed", "text": "", "o_bytes": 0,
                "elapsed": 0.0, "err": str(e)[:200]}
    status = "ok"
    while True:
        rc = proc.poll()
        if rc is not None:
            break
        try:
            sz = os.path.getsize(op) if os.path.isfile(op) else 0
        except OSError:
            sz = 0
        if sz > MAX_O_BYTES:
            proc.kill()
            proc.wait()
            status = "oversize"
            break
        if time.time() - t0 > timeout:
            proc.kill()
            proc.wait()
            status = "timeout"
            break
        time.sleep(0.2)
    elapsed = time.time() - t0
    text = ""
    sz = 0
    if os.path.isfile(op):
        try:
            sz = os.path.getsize(op)
            with open(op, "rb") as f:
                text = f.read().decode("utf-8", "replace")
        except OSError:
            pass
    if status == "ok" and not text:
        status = "no_output"
    # 及时清掉大文件（结果已在内存）
    for p in (op, rp):
        try:
            os.remove(p)
        except OSError:
            pass
    return {"status": status, "text": text, "o_bytes": sz, "elapsed": elapsed}


# ------------------------------------------------------------------ data loading
def load_inputs():
    tasks = {}
    task_order = []
    with open(os.path.join(BENCH, "tasks.jsonl"), encoding="utf-8") as f:
        for line in f:
            if line.strip():
                t = json.loads(line)
                tasks[t["task_id"]] = t
                task_order.append(t["task_id"])
    valid = set()
    with open(os.path.join(BENCH, "expected.jsonl"), encoding="utf-8") as f:
        for line in f:
            if line.strip():
                e = json.loads(line)
                if e.get("valid"):
                    valid.add(e["task_id"])
    return tasks, valid, task_order


def load_agent_rows():
    """主实验逐题记录。run_results_kon_w*.jsonl 是 8 worker 的原始主批；
    run_results_kon.jsonl 只有 1 条补跑记录，按 task_id 覆盖。"""
    rows = []
    for p in sorted(glob.glob(os.path.join(BENCH, "run_results_kon_w*.jsonl"))):
        with open(p, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    rows.append(json.loads(line))
    last = {}
    for r in rows:
        last[r["task_id"]] = r
    p1 = os.path.join(BENCH, "run_results_kon.jsonl")
    if os.path.isfile(p1):
        with open(p1, encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    r = json.loads(line)
                    last[r["task_id"]] = r
    return last


# ---- 主实验 A 批终版卡重建 ------------------------------------------------
# 背景：decks_kon 被 HALF/ORAL/KAPPA 等批次共用同名归档，后续批次会覆盖
# A 批的卡。核实证据：135 张卡的 mtime 晚于 A 批结果，且内容与 A 批 trace
# 的最后一次写盘不同。为保证重判的是"主实验真正判过的那张卡"，这里按
# tools/files.py 的 write_file / edit_file 语义回放 A 批 trace，重建终版卡。
def _norm_path(p):
    return str(p or "").replace("\\", "/").lstrip("./")


def _find_a_trace(tid, produced_abs):
    if produced_abs:
        tp = os.path.join(os.path.dirname(produced_abs), "traces", tid + "_r1.json")
        if os.path.isfile(tp):
            return tp
    cands = glob.glob(os.path.join(ROOT, "workspace*", "traces", tid + "_r1.json"))
    cands = sorted(cands, key=lambda p: (0 if "workspace_kon_w" in p else 1, p))
    return cands[0] if cands else None


def reconstruct_a_deck(task, rec):
    """按 A 批 trace 回放得到该题终版卡。返回 (text|None, trace_path|str)。"""
    produced = rec.get("produced") or ""
    if not produced:
        return None, ""
    tp = _find_a_trace(task["task_id"], rec.get("produced_abs") or "")
    if not tp:
        return None, ""
    try:
        with open(tp, encoding="utf-8", errors="replace") as f:
            tr = (json.load(f).get("trace") or [])
    except Exception:  # noqa: BLE001
        return None, tp
    files = {}
    if task.get("context_name") and task.get("context_deck"):
        files[_norm_path(task["context_name"])] = task["context_deck"]
    for x in tr:
        tool, a = x.get("tool"), (x.get("args") or {})
        if tool == "write_file" and a.get("text") is not None:
            files[_norm_path(a.get("path"))] = a["text"]
        elif tool == "edit_file":
            p = _norm_path(a.get("path"))
            old, new = a.get("old"), a.get("new")
            if p in files and isinstance(old, str) and isinstance(new, str) and old in files[p]:
                files[p] = files[p].replace(old, new, 1)
    return files.get(_norm_path(produced)), tp


# ------------------------------------------------------------------ batch driver
def _run_chunk(job):
    """一个 worker 的顺序任务块。job=(idx, [items], out_path, timeout, rel_tol)。"""
    idx, items, out_path, timeout, rel_tol = job
    workdir = os.path.join(DEFAULT_OUT, "_work", f"w{idx}")
    _prepare_worker_dir(workdir)
    out = []
    t_start = time.time()
    for k, item in enumerate(items):
        tid, deck_text, family = item["task_id"], item["deck"], item["family"]
        src = item.get("source", "")
        if deck_text is None:
            rec = {"task_id": tid, "family": family, "exec_ok_new": False,
                   "reason": "no_deck", "final_time": None,
                   "converged_metric": None, "detail": "", "elapsed": 0.0,
                   "o_bytes": 0, "status": "no_deck", "deck_source": src}
        else:
            rr = run_deck(deck_text, workdir, timeout=timeout)
            if rr["status"] != "ok":
                rec = {"task_id": tid, "family": family, "exec_ok_new": False,
                       "reason": rr["status"], "final_time": None,
                       "converged_metric": None,
                       "detail": rr.get("err", ""), "elapsed": rr["elapsed"],
                       "o_bytes": rr["o_bytes"], "status": rr["status"],
                       "deck_source": src}
            else:
                ev = evaluate_text(rr["text"], deck_text, family, rel_tol=rel_tol)
                rec = {"task_id": tid, "family": family, **ev,
                       "elapsed": rr["elapsed"], "o_bytes": rr["o_bytes"],
                       "status": "ok", "deck_source": src}
        out.append(rec)
        if (k + 1) % 10 == 0:
            print(f"[w{idx}] {k+1}/{len(items)} last={tid} ok={rec['exec_ok_new']} "
                  f"reason={rec['reason']} t={time.time()-t_start:.0f}s", flush=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for r in out:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    return out_path


def run_batch(items, workers=8, timeout=900.0, rel_tol=0.01, tag="batch"):
    """8 进程并行；每进程独立工作目录。items: [{task_id, deck, family}]。"""
    os.makedirs(os.path.join(DEFAULT_OUT, "_work"), exist_ok=True)
    chunks = [[] for _ in range(workers)]
    for i, it in enumerate(items):
        chunks[i % workers].append(it)          # 交替分块，长题分散
    jobs = []
    for idx, chunk in enumerate(chunks):
        if chunk:
            jobs.append((idx, chunk, os.path.join(DEFAULT_OUT, f"_{tag}_w{idx}.jsonl"),
                         timeout, rel_tol))
    t0 = time.time()
    with mp.Pool(processes=len(jobs)) as pool:
        outs = pool.map(_run_chunk, jobs)
    recs = []
    for p in outs:
        with open(p, encoding="utf-8") as f:
            recs += [json.loads(x) for x in f if x.strip()]
    print(f"[{tag}] done {len(recs)} in {time.time()-t0:.0f}s", flush=True)
    return recs


# ------------------------------------------------------------------ main
def build_items(kind, tasks, valid, deck_source="a_trace"):
    items = []
    if kind == "calib":
        for tid in sorted(valid):
            t = tasks[tid]
            items.append({"task_id": tid, "deck": t.get("reference"),
                          "family": t.get("family"), "source": "reference"})
        return items
    # rejudge：324 道 VALID 题的智能体终版卡；无卡者记 no_deck
    last = load_agent_rows()
    for tid in sorted(valid):
        t = tasks[tid]
        deck = None
        src = "no_deck"
        if deck_source == "a_trace":
            rec = last.get(tid, {})
            deck, tp = reconstruct_a_deck(t, rec)
            if deck is not None:
                src = "a_trace"
            elif rec.get("produced"):
                # 回放失败但 A 批确有产物：退回 decks_kon（如实标记来源）
                p = os.path.join(BENCH, "decks_kon", tid + ".i")
                if os.path.isfile(p):
                    with open(p, encoding="utf-8", errors="replace") as f:
                        deck = f.read()
                    src = "kon_fallback"
            # produced 为空 = A 批没有可判的终版卡 → no_deck（不得借用后续批次卡）
        else:
            p = os.path.join(BENCH, "decks_kon", tid + ".i")
            if os.path.isfile(p):
                with open(p, encoding="utf-8", errors="replace") as f:
                    deck = f.read()
                src = "kon"
        items.append({"task_id": tid, "deck": deck, "family": t.get("family"),
                      "source": src, "old": last.get(tid, {})})
    return items


def main():
    global DEFAULT_OUT
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=["calib", "rejudge"])
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--timeout", type=float, default=900.0)
    ap.add_argument("--rel-tol", type=float, default=0.01)
    ap.add_argument("--deck-source", choices=["a_trace", "kon"], default="a_trace",
                    help="rejudge 的卡来源：a_trace=从主实验 A 批 trace 回放（默认，"
                         "避免 decks_kon 被后续批次覆盖）；kon=直接用 decks_kon")
    ap.add_argument("--outdir", default=DEFAULT_OUT)
    a = ap.parse_args()
    DEFAULT_OUT = a.outdir
    os.makedirs(DEFAULT_OUT, exist_ok=True)
    tasks, valid, _order = load_inputs()
    items = build_items(a.mode, tasks, valid, deck_source=a.deck_source)
    tag = a.mode if a.mode == "calib" else f"{a.mode}_{a.deck_source}"
    recs = run_batch(items, workers=a.workers, timeout=a.timeout,
                     rel_tol=a.rel_tol, tag=tag)
    if a.mode == "rejudge":
        last = load_agent_rows()
        for r in recs:
            r["exec_ok_old"] = bool(last.get(r["task_id"], {}).get("exec_ok"))
    out = os.path.join(DEFAULT_OUT, f"_{tag}_results.jsonl")
    with open(out, "w", encoding="utf-8") as f:
        for r in recs:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    n = len(recs)
    ok = sum(1 for r in recs if r["exec_ok_new"])
    print(f"{a.mode}: pass {ok}/{n} = {ok/n:.2%} -> {out}")


if __name__ == "__main__":
    main()
