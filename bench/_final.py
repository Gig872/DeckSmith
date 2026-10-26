# -*- coding: utf-8 -*-
"""最终数据汇总（修正去重规则）。

去重规则：同一 (题, 轮) 取**"真的评到了"**的那条——
  n_errors 非 None  = 评测时找到了产物卡，是有效判定
  n_errors 为 None  = 评测时产物卡缺失，是无效判定（可能被并发/中断污染）
有效判定优先于无效判定；同等级取后者。
"""
import glob
import json
import math
import os
from collections import Counter, defaultdict

BENCH = r"C:\relap-5\agent-kit\bench"
DATA = r"C:\relap-5\论文\数据"


def wcsv(name, text):
    """写 CSV；被 Excel 等占用时改存 .new，不让脚本整体崩掉。"""
    p = os.path.join(DATA, name)
    try:
        with open(p, "w", encoding="utf-8-sig") as f:
            f.write(text)
    except PermissionError:
        with open(p + ".new", "w", encoding="utf-8-sig") as f:
            f.write(text)
        print("[占用] %s 已锁，改存 %s.new" % (name, name))


def load(pat):
    rows = []
    for p in glob.glob(os.path.join(BENCH, pat)):
        for line in open(p, encoding="utf-8", errors="replace"):
            try:
                rows.append(json.loads(line))
            except Exception:
                pass
    return rows


def better(a, b):
    if a is None:
        return b
    if b is None:
        return a
    a_ok = a.get("n_errors") is not None
    b_ok = b.get("n_errors") is not None
    if a_ok != b_ok:
        return a if a_ok else b
    return b


def U(pat, tag=None, cond=None):
    u = {}
    for r in load(pat):
        if tag is not None and str(r.get("tag") or "") != tag:
            continue
        if cond is not None and str(r.get("knowledge") or "") != cond:
            continue
        k = (r["task_id"], r.get("repeat", 1))
        u[k] = better(u.get(k), r)
    return u


def rate(recs, key):
    if not recs:
        return None
    if key == "exec":
        v = [bool(r.get("exec_ok")) for r in recs]
    elif key == "phys":
        v = [bool(r.get("exec_ok") and r.get("phys_ok")) for r in recs]
    elif key == "sem":
        v = [bool(r.get("sem_ok")) for r in recs]
    elif key == "first":
        v = [bool(r.get("exec_ok_first")) for r in recs if r.get("exec_ok_first") is not None]
    else:
        v = []
    return (len(v), 100.0 * sum(1 for x in v if x) / len(v)) if v else None


L = []
# ---------- 主批次 ----------
A = U("run_results_kon_w*.jsonl", tag="", cond="on")
A2 = U("run_results_kon.jsonl", tag="", cond="on")
for k, r in A2.items():
    A[k] = better(A.get(k), r)
B = U("run_results_koff_w*.jsonl")
K = U("run_results_kon_kappa_w*.jsonl")
H = U("run_results_kon_half_w*.jsonl")
O = U("run_results_kon_oral_w*.jsonl")
KP = U("run_results_kon_keep_w*.jsonl")

L.append("=== 主批次（修正去重后）===")
for name, u in (("A 带库全量", A), ("B 无库57", B), ("keep 补充", KP), ("half", H), ("oral", O)):
    rs = [r for (t, rp), r in u.items() if rp == 1]
    e, p_, s = rate(rs, "exec"), rate(rs, "phys"), rate(rs, "sem")
    L.append("  %-10s N=%3d  exec=%s  phys=%s  sem=%s" % (
        name, len(rs), "%.1f" % e[1] if e else "-",
        "%.1f" % p_[1] if p_ else "-", "%.1f" % s[1] if s else "-"))
bad = sum(1 for (t, rp), r in list(A.items()) + list(K.items())
          if r.get("produced") and r.get("n_errors") is None and not r.get("exec_ok"))
L.append("  仍无效的记录数（A+κ）: %d" % bad)

# ---------- 基线 ----------
L.append("")
L.append("=== 基线（按轮）===")
gb = defaultdict(lambda: defaultdict(dict))
for r in load("baseline_results*.jsonl"):
    gb[r.get("baseline")][r.get("repeat", 1)][r["task_id"]] = r  # 按题去重
_t16 = "基线,轮次,N,exec%,phys%,sem%\n"
for b in sorted(gb):
    for rp in sorted(gb[b], key=lambda x: (x is None, x)):
        rs = list(gb[b][rp].values())
        e, p_, s = rate(rs, "exec"), rate(rs, "phys"), rate(rs, "sem")
        L.append("  %-14s 轮%s N=%d exec=%.1f phys=%.1f sem=%.1f" % (
            b, rp, len(rs), e[1], p_[1], s[1]))
        _t16 += "%s,%s,%d,%.1f,%.1f,%.1f\n" % (b, rp, len(rs), e[1], p_[1], s[1])
wcsv("16_基线三轮.csv", _t16)

# ---------- 四档语域 ----------
kids = sorted(set(t for (t, rp) in KP if rp == 1))
L.append("")
L.append("=== 语域四档（共同 %d 题）===" % len(kids))
lev = [("ENG", A), ("HALF", H), ("ORAL", O), ("KEEP", KP)]


def pick(u, t):
    return u.get((t, 1))


_t15 = "档位,N,exec%,phys%,sem%,first%\n"
for tag, u in lev:
    rs = [pick(u, t) for t in kids if pick(u, t)]
    e, p_, s, fi = (rate(rs, "exec"), rate(rs, "phys"), rate(rs, "sem"), rate(rs, "first"))
    L.append("  %-6s N=%d exec=%.1f phys=%.1f sem=%.1f first=%.1f" % (
        tag, len(rs), e[1], p_[1], s[1], fi[1]))
    _t15 += "%s,%d,%.1f,%.1f,%.1f,%.1f\n" % (tag, len(rs), e[1], p_[1], s[1], fi[1])
_t15 += "\n对比,指标,含义,b,c,差值pp,CI下,CI上,判定\n"
for name, u1, u2, note in (("ENG-KEEP", A, KP, "纯语域"),
                           ("KEEP-ORAL", KP, O, "纯删冗余"),
                           ("ENG-ORAL", A, O, "合计")):
    for key in ("exec", "phys", "sem"):
        b = c = n = 0
        for t in kids:
            r1, r2 = pick(u1, t), pick(u2, t)
            if not r1 or not r2:
                continue
            if key == "phys":
                v1, v2 = bool(r1.get("exec_ok") and r1.get("phys_ok")), bool(r2.get("exec_ok") and r2.get("phys_ok"))
            else:
                fld = "exec_ok" if key == "exec" else "sem_ok"
                v1, v2 = bool(r1.get(fld)), bool(r2.get(fld))
            n += 1
            if v1 and not v2:
                b += 1
            elif not v1 and v2:
                c += 1
        if n == 0 or b + c == 0:
            continue
        d = (c - b) / n
        se = math.sqrt(max(0.0, (b + c) - (b - c) ** 2 / n)) / n
        lo, hi = (d - 1.96 * se) * 100, (d + 1.96 * se) * 100
        vd = "等价" if (lo >= -10 and hi <= 10) else ("有差异" if (lo > 0 or hi < 0) else "不确定")
        _t15 += "%s,%s,%s,%d,%d,%.1f,%.1f,%.1f,%s\n" % (name, key, note, b, c, d * 100, lo, hi, vd)
wcsv("15_四档对照.csv", _t15)

open(r"C:\relap-5\论文\_final_data.txt", "w", encoding="utf-8").write("\n".join(L))
print("\n".join(L))
