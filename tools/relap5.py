# -*- coding: utf-8 -*-
"""RELAP5 领域工具：run_relap5（真跑）/ parse_output（解析 .o）/ validate_i（最小静态校验）。

沙箱：输入文件在 workspace 内；产物写到 workspace/runs/（不裸存 relap5 目录）；
relap5 运行 cwd = 含 tpf* 物性文件的目录（否则找不到物性文件）。
"""
from __future__ import annotations

import hashlib
import re
import subprocess
import time
from pathlib import Path

from registry import tool
from safety import Sandbox
from config import load, relap5_paths

_SB = Sandbox(load().workspace)
_CTRL = {" ", "0", "1", "+"}
_SEQ = 0   # 进程内递增，保证输出名唯一（即使同秒、同前缀）


def _next_seq() -> int:
    global _SEQ
    _SEQ += 1
    return _SEQ


def _clean(raw: str) -> str:
    out = []
    for line in raw.split("\n"):
        if line and line[0] in _CTRL:
            out.append(line[1:].rstrip("\r"))
        else:
            out.append(line.rstrip("\r"))
    return "\n".join(out)


def _normal_end(t: str) -> bool:
    tail = t[-3000:]
    return ("Transient terminated" in tail) or ("input processing completed successfully" in tail)


def _errors(t: str, n: int = 8) -> list[str]:
    return [ln.strip()[:200] for ln in t.split("\n") if "********" in ln][:n]


def _read_o(p: Path) -> str:
    return p.read_bytes().decode("utf-8", "replace")


def _prune_runs(outdir: Path, keep: int) -> None:
    """只保留最近 keep 次运行（.o/.r 按主干成组），删更早的；keep<=0 表示不清理。"""
    if keep <= 0:
        return
    try:
        groups: dict[str, list[Path]] = {}
        for p in outdir.iterdir():
            if p.is_file():
                groups.setdefault(p.stem, []).append(p)
    except OSError:
        return
    if len(groups) <= keep:
        return
    ordered = sorted(groups.values(),
                     key=lambda g: max(f.stat().st_mtime for f in g), reverse=True)
    for g in ordered[keep:]:
        for f in g:
            try:
                f.unlink()
            except OSError:
                pass


@tool("validate_i", "对一段 RELAP5 输入卡做最小静态检查（终止卡/卡号/注释行/引号）。",
      {"text": {"type": "string"}}, ["text"])
def validate_i(text: str) -> str:
    probs = []
    raw = text.splitlines()
    # 1) 注释行纪律：非空行必须以 * / = / . / 数字 开头；否则 RELAP5 会当卡读 → 报错。
    #    （实测踩坑：说明文字若不以 * 开头，会报 Unrecognizable card number）
    for s in (x.strip() for x in raw):
        if not s:
            continue
        if s[0] in ("*", "=", ".", "/") or s[0].isdigit():
            continue
        probs.append(f"疑似非法行（注释必须以 * 或 = 开头，否则被当卡读）：{s[:60]}")
        break
    code = [l.strip() for l in raw if l.strip() and not l.strip().startswith(("*", "="))]
    if not any(l in (".", "/") for l in code):
        probs.append("缺少终止卡（独占一行 . 或 /）")
    for l in code:
        if '"' in l:
            probs.append(f"行内含引号注释（RELAP5 不支持）：{l[:50]}")
            break
        head = l.split()[0]
        # 合法卡号长度 3(控制卡)~8(热构件/通用表/堆动力学，如 1CCCGXNN、30000000)；
        # 只有 >8 位才判异常（曾误报 8 位热构件卡，害 agent 白改卡号）。
        if head.isdigit() and len(head) > 8:
            probs.append(f"部件卡号位数异常（>8 位）：{head}")
            break
    return "\n".join(probs) if probs else "静态检查通过（无明显低级错误）。"


@tool("run_relap5", "真跑一个 RELAP5 输入文件（相对工作目录），返回 rc 与结果摘要。",
      {"i_path": {"type": "string", "description": "工作目录内的 .i 文件路径"},
       "timeout": {"type": "integer"}}, ["i_path"])
def run_relap5(i_path: str, timeout: int = 180) -> str:
    exe, rdir = relap5_paths()
    if not exe.is_file():
        return f"[relap5] 未找到可执行文件（配置 config.json 的 relap5_dir/relap5_exe）。当前={exe}"
    ip = _SB.resolve(i_path)
    if not ip.is_file():
        return f"[relap5] 输入文件不存在: {i_path}"
    outdir = _SB.root / "runs"
    outdir.mkdir(parents=True, exist_ok=True)
    st = time.strftime("%Y%m%d_%H%M%S")
    # 关键：RELAP5 对 -o/-r 路径有 ~80 字符缓冲上限，路径过长会静默截断扩展名，
    # 导致找不到 .o。故输出用"短名"：截断 stem + 4 位哈希（区分同前缀输入）+ 进程内序号
    # （区分同秒多次运行），保证整条路径远低于上限且**绝不撞名**。
    safe = re.sub(r"[^A-Za-z0-9_]", "_", ip.stem)[:12]
    h4 = hashlib.md5(ip.stem.encode("utf-8")).hexdigest()[:4]
    base = f"{safe}_{h4}_{_next_seq():04d}"
    o = outdir / f"{base}.o"
    r = outdir / f"{base}.r"
    for f in (o, r):                       # RELAP5 不覆盖已存在文件，先清目标
        try:
            f.unlink()
        except FileNotFoundError:
            pass
    for name in ("rstplt", "plotfl", "stripf"):   # 清 RELAP5 在自身目录写的临时输出
        fp = Path(rdir) / name
        if fp.is_file():
            try:
                fp.unlink()
            except OSError:
                pass
    cmd = [str(exe), "-i", str(ip), "-o", str(o), "-r", str(r)]
    try:
        p = subprocess.run(cmd, cwd=str(rdir), capture_output=True,
                           timeout=min(int(timeout), 300), text=True, errors="replace")
    except subprocess.TimeoutExpired:
        return "[relap5] 运行超时，已终止。"
    except Exception as e:  # noqa: BLE001
        return f"[relap5] 执行失败: {e}"
    if not o.is_file() and (outdir / base).is_file():   # 万一仍被截断：兜底认无扩展名文件
        o = outdir / base
    if not o.is_file():
        return f"[relap5] rc={p.returncode}，但 .o 未生成（可能启动失败）。"
    t = _clean(_read_o(o))
    ok = _normal_end(t)
    errs = _errors(t)
    rel = o.relative_to(_SB.root)
    _prune_runs(outdir, int(getattr(load(), "runs_keep", 50) or 0))   # 保留最近 N 次，防无限增长
    msg = f"[relap5] rc={p.returncode} 正常结束={ok}  输出={rel}"
    if errs:
        msg += "\n错误：\n" + "\n".join(errs)
    return msg


@tool("parse_output", "解析 RELAP5 输出(.o)：返回是否正常结束、错误行、尾部。",
      {"o_path": {"type": "string"}, "max_chars": {"type": "integer"}}, ["o_path"])
def parse_output(o_path: str, max_chars: int = 1200) -> str:
    p = _SB.resolve(o_path)
    if not p.is_file():
        return f"[parse] 文件不存在: {o_path}"
    t = _clean(_read_o(p))
    errs = _errors(t)
    head = f"正常结束={_normal_end(t)}  错误数={len(errs)}"
    body = ("\n错误：\n" + "\n".join(errs)) if errs else ""
    tail = "\n--- 尾部 ---\n" + t[-int(max_chars):]
    return head + body + tail


# ---------------- 结果物理校验（守恒 / 量级；不是画图） ----------------

_HDR_STATE = re.compile(r"^\s*\d?\s*Vol\.no\..*pressure.*temp(f|g)?.*$", re.M)
_ANY_VOLNO = re.compile(r"^\s*\d?\s*Vol\.no\.", re.M)
_ROWV = re.compile(r"^\s*(\d{3}-\d{6})\s+(.*)$")
_HDR_JUN = re.compile(r"^\s*\d?\s*Jun\.no\..*mass\s+flow.*$", re.M)
_ANY_JUN = re.compile(r"^\s*\d?\s*Jun\.no\.", re.M)


def _final_state(t: str):
    """取最后一张状态表（含 pressure/tempf/tempg 列），按表头名对位列。"""
    hdrs = list(_HDR_STATE.finditer(t))
    if not hdrs:
        return {}, []
    h = hdrs[-1]
    names = h.group(0).split()
    idx = {k: (names.index(k) if k in names else None)
           for k in ("pressure", "tempf", "tempg", "voidg")}
    rows = []
    for ln in t[h.end():].split("\n"):
        if _ANY_VOLNO.match(ln):     # 进入下一张表 → 停
            break
        if _ROWV.match(ln):
            rows.append(ln.split())
    return idx, rows


@tool("check_sanity", "结果物理校验：从 .o 抽 最终压力/温度 极值 与 质量守恒误差，判定是否物理合理。"
                     "交付前必用；合理性不过关不得交付。",
      {"o_path": {"type": "string"}}, ["o_path"])
def check_sanity(o_path: str) -> str:
    p = _SB.resolve(o_path)
    if not p.is_file():
        return f"[sanity] 文件不存在: {o_path}"
    t = _clean(_read_o(p))
    out, flags = [], []

    # 1) 是否正常结束 + 最终时间
    ok = _normal_end(t)
    ft = None
    m = re.findall(r"Final time=\s*([\d.Ee+-]+)", t)
    if m:
        ft = m[-1]
    if not ok:
        flags.append("[错误] 未正常结束（有致命错误或提前终止）")

    # 2) 最终状态表的压力/温度极值
    idx, rows = _final_state(t)
    ps, ts = [], []
    for tk in rows:
        try:
            if idx.get("pressure") is not None:
                ps.append(float(tk[idx["pressure"]]))
            for k in ("tempf", "tempg"):
                j = idx.get(k)
                if j is not None:
                    v = float(tk[j])
                    if 100.0 < v < 6000.0:      # 滤掉哨兵值
                        ts.append(v)
        except (ValueError, IndexError):
            pass
    if ps:
        out.append(f"压力范围: {min(ps):.3g} ~ {max(ps):.3g} Pa")
        if min(ps) <= 0:
            flags.append("[错误] 存在非正压力（物理上不可能）")
    if ts:
        out.append(f"温度范围: {min(ts):.1f} ~ {max(ts):.1f} K")
        if max(ts) > 900 or min(ts) < 250:
            flags.append(f"[警告] 温度极值 {min(ts):.0f}~{max(ts):.0f} K 超出常温水/蒸汽合理范围，"
                         "先确认是否读错表，再查边界/能量是否自洽")
    if not ps and not ts:
        out.append("(未能定位最终状态表——请人工确认)")

    # 3) 质量守恒（RELAP5 自报 mass error）。
    #    注意：瞬态排空时末态质量很小，用"末态质量"当分母会把相对误差**虚高**
    #    （曾把 0.4% 的绝对误差算成 19.7%，把 agent 带偏）。故以**过程中最大质量≈初始**为基准。
    me = re.findall(r"mass\s*=\s*([\d.Ee+-]+)\s*kg\s+mass error=\s*([\d.Ee+-]+)", t)
    if me:
        m_last, err = float(me[-1][0]), float(me[-1][1])
        m_ref = max(float(a) for a, _b in me) or 1.0
        ratio = abs(err) / m_ref
        out.append(f"质量守恒: 末态质量≈{m_last:.4g} kg（初始≈{m_ref:.4g}）, "
                   f"累计质量误差≈{err:.3g} kg（占初始 {ratio:.2%}）")
        if ratio > 0.05:
            flags.append(f"[错误] 质量严重不守恒（误差占初始 {ratio:.1%}）——"
                         "边界条件多半不自洽（如定了入口流量却无对应排出）或未收敛")
        elif ratio > 0.01:
            flags.append(f"[警告] 质量误差偏高（占初始 {ratio:.1%}），建议核查边界与时间步")

    verdict = "物理合理性：通过（未发现守恒/量级硬伤）" if not flags else \
              "物理合理性：**存疑**，见下列问题"
    return (f"[check_sanity] 正常结束={ok}  最终时间={ft}\n"
            + "\n".join(out)
            + "\n" + verdict
            + ("\n" + "\n".join(flags) if flags else "")
            + "\n（此工具只查守恒与量级；请再与你在建模意图里写下的预判范围核对。"
            "需要具体数值用 result_summary。）")


def _final_junctions(t: str):
    """取最后一张接管表（含 from/to/mass flow 列）。列为定序：
    0=接管号 1=来向 2=去向 3=液速 4=汽速 5=质量流量 6=面积 7=喉部比。"""
    hdrs = list(_HDR_JUN.finditer(t))
    if not hdrs:
        return []
    h = hdrs[-1]
    rows = []
    for ln in t[h.end():].split("\n"):
        if _ANY_JUN.match(ln):       # 下一张接管表 → 停
            break
        m = _ROWV.match(ln)
        if m and len(ln.split()) >= 7:
            rows.append(ln.split())
    return rows


def _vol_key(vid: str):
    """'−110-010001' / '110-010001' → '110-01'（控制体键：部件号-体号）。"""
    m = re.match(r"-?(\d{3})-(\d{2})", vid or "")
    return f"{m.group(1)}-{m.group(2)}" if m else None


def _boundary_comps(t: str) -> set:
    """从 'Input data for component 101, inb tmdpvol having ...' 抽出时间相关边界部件号。"""
    b = set()
    for m in re.finditer(r"component\s+(\d+),\s+\S+\s+(\S+)\s+having", t):
        if "tmdp" in m.group(2).lower():
            b.add(m.group(1))
    return b


def _node_balance(t: str):
    """各控制体净流量（+为净流入）。按接管表逐条累加：to 记 +q、from 记 −q。
    返回 {key: (net, throughput)}。"""
    net: dict[str, float] = {}
    thru: dict[str, float] = {}
    for tk in _final_junctions(t):
        try:
            fk, tkk, q = _vol_key(tk[1]), _vol_key(tk[2]), float(tk[5])
        except (ValueError, IndexError):
            continue
        if fk:
            net[fk] = net.get(fk, 0.0) - q
            thru[fk] = thru.get(fk, 0.0) + abs(q)
        if tkk:
            net[tkk] = net.get(tkk, 0.0) + q
            thru[tkk] = thru.get(tkk, 0.0) + abs(q)
    return net, thru


@tool("result_summary", "结果摘要（可信读数）：直接给出 最终各控制体 压力/温度/空泡 与 各接管 质量流量/流速。"
                        "交付里要引用具体数值时，一律用它，**不要**再用 python_exec 去翻 .o（易读错列）。",
      {"o_path": {"type": "string"}, "max_rows": {"type": "integer"}}, ["o_path"])
def result_summary(o_path: str, max_rows: int = 40) -> str:
    p = _SB.resolve(o_path)
    if not p.is_file():
        return f"[result] 文件不存在: {o_path}"
    t = _clean(_read_o(p))
    n = int(max_rows)
    m = re.findall(r"Final time=\s*([\d.Ee+-]+)", t)
    lines = [f"[result_summary] 正常结束={_normal_end(t)}  最终时间={m[-1] if m else '?'}"]

    # 系统质量 / 守恒
    me = re.findall(r"mass\s*=\s*([\d.Ee+-]+)\s*kg\s+mass error=\s*([\d.Ee+-]+)", t)
    if me:
        m_last, err = float(me[-1][0]), float(me[-1][1])
        m_ref = max(float(a) for a, _b in me) or 1.0
        lines.append(f"末态质量≈{m_last:.4g} kg（初始≈{m_ref:.4g}）  累计质量误差≈{err:.3g} kg"
                     f"（占初始 {abs(err)/m_ref:.2%}）")

    # 控制体状态
    idx, vrows = _final_state(t)
    if vrows:
        lines.append("— 控制体 (最终) —")
        for tk in vrows[:n]:
            try:
                vid = tk[0]
                pv = tk[idx["pressure"]] if idx.get("pressure") is not None else "?"
                tv = tk[idx["tempf"]] if idx.get("tempf") is not None else "?"
                vg = tk[idx["voidg"]] if idx.get("voidg") is not None else "?"
                lines.append(f"  {vid}  P={pv} Pa  Tf={tv} K  voidg={vg}")
            except (IndexError, KeyError):
                pass

    # 接管流量
    jrows = _final_junctions(t)
    if jrows:
        lines.append("— 接管 (最终) —")
        for tk in jrows[:n]:
            try:
                lines.append(f"  {tk[0]}  {tk[1]} -> {tk[2]}  质量流量={tk[5]} kg/s  液速={tk[3]} m/s")
            except IndexError:
                pass
        # 拓扑检查：同一对控制体被多个接管重复连接 = 冗余/错误连接
        seen: dict[str, int] = {}
        for tk in jrows:
            try:
                seen[f"{tk[1]} -> {tk[2]}"] = seen.get(f"{tk[1]} -> {tk[2]}", 0) + 1
            except IndexError:
                pass
        dups = [k for k, v in seen.items() if v > 1]
        if dups:
            lines.append("[警告] 重复连接（同一对控制体被接了多次）: " + "; ".join(dups)
                         + " —— 多半多接了一条冗余接管，应只保留一条")

    # 节点流量平衡：每个控制体 进=出（时间相关边界部件除外，它们本就允许净流量）
    net, thru = _node_balance(t)
    if net:
        bcomps = _boundary_comps(t)
        bad = []
        for k, v in sorted(net.items()):
            if k.split("-")[0] in bcomps:
                continue
            tol = max(1e-3, 0.01 * thru.get(k, 0.0))
            if abs(v) > tol:
                bad.append(f"{k} 净流量={v:+.4g} kg/s (吞吐≈{thru.get(k, 0.0):.4g})")
        lines.append("— 节点流量平衡 —")
        lines.append("  所有内部节点 进=出（守恒）" if not bad
                     else "[警告] 以下控制体净流量≠0（不守恒，疑似未收敛或边界/拓扑错误）:\n    "
                          + "\n    ".join(bad))

    if not vrows and not jrows:
        lines.append("(未能定位最终状态/接管表——请人工确认)")
    return "\n".join(x for x in lines if x != "")


# ---------------- 时间历程提取（瞬态分析用；不是画图） ----------------

_TIME = re.compile(r"time=\s*([\d.Ee+-]+)")


def _series_flow(t: str) -> list:
    """抽 各编辑时刻的接管质量流量：[(time, {junid: flow}), ...]（同时刻取最后一次）。"""
    lines = t.split("\n")
    cur, i, by_t = None, 0, {}
    while i < len(lines):
        m = _TIME.search(lines[i])
        if m:
            try:
                cur = float(m.group(1))
            except ValueError:
                pass
        if _HDR_JUN.match(lines[i]):
            rows, j = [], i + 1
            while j < len(lines) and not _ANY_JUN.match(lines[j]):
                if _ROWV.match(lines[j]) and len(lines[j].split()) >= 7:
                    rows.append(lines[j].split())
                j += 1
            if rows and cur is not None:
                by_t[cur] = {tk[0]: tk[5] for tk in rows}
            i = j
            continue
        i += 1
    return sorted(by_t.items())


def _series_volume(t: str) -> list:
    """抽 各编辑时刻的 逐控制体温度：[(time, {volid: tempf}), ...]。"""
    lines = t.split("\n")
    cur, i, by_t = None, 0, {}
    while i < len(lines):
        m = _TIME.search(lines[i])
        if m:
            try:
                cur = float(m.group(1))
            except ValueError:
                pass
        if _HDR_STATE.match(lines[i]):
            names = lines[i].split()
            itf = names.index("tempf") if "tempf" in names else None
            d, j = {}, i + 1
            while j < len(lines) and not _ANY_VOLNO.match(lines[j]):
                if _ROWV.match(lines[j]) and itf is not None:
                    tk = lines[j].split()
                    try:
                        d[tk[0]] = float(tk[itf])
                    except (ValueError, IndexError):
                        pass
                j += 1
            if d and cur is not None:
                by_t[cur] = d
            i = j
            continue
        i += 1
    return sorted(by_t.items())


def _series_state(t: str) -> list:
    """抽 各编辑时刻的 压力/温度极值：[(time, minP, maxP, minT, maxT), ...]。"""
    lines = t.split("\n")
    cur, i, by_t = None, 0, {}
    while i < len(lines):
        m = _TIME.search(lines[i])
        if m:
            try:
                cur = float(m.group(1))
            except ValueError:
                pass
        if _HDR_STATE.match(lines[i]):
            names = lines[i].split()
            ip = names.index("pressure") if "pressure" in names else None
            itf = names.index("tempf") if "tempf" in names else None
            itg = names.index("tempg") if "tempg" in names else None
            ps, ts, j = [], [], i + 1
            while j < len(lines) and not _ANY_VOLNO.match(lines[j]):
                if _ROWV.match(lines[j]):
                    tk = lines[j].split()
                    try:
                        if ip is not None:
                            ps.append(float(tk[ip]))
                        for k in (itf, itg):
                            if k is not None:
                                v = float(tk[k])
                                if 100.0 < v < 6000.0:
                                    ts.append(v)
                    except (ValueError, IndexError):
                        pass
                j += 1
            if ps and cur is not None:
                by_t[cur] = (min(ps), max(ps), min(ts) if ts else 0, max(ts) if ts else 0)
            i = j
            continue
        i += 1
    return sorted(by_t.items())


@tool("transient_history",
      "瞬态时间历程：从 .o 抽 各时刻的 接管质量流量 / 逐控制体温度 / 压力温度极值，给出**随时间变化**的"
      "曲线数据。瞬态题核对'流量/温度随时间怎么变'时用它，**不要**用 python_exec 手抠 .o。",
      {"o_path": {"type": "string"},
       "what": {"type": "string", "description": "flow(接管流量) / volume(逐控制体温度) / state(压力温度极值)"},
       "ids": {"type": "array", "description": "只取这些部件号（接管如 ['102-000000'] 或控制体如 ['120-040000']）",
               "items": {"type": "string"}},
       "max_points": {"type": "integer", "description": "最多给多少个时刻，默认 30"}},
      ["o_path"])
def transient_history(o_path: str, what: str = "flow", ids=None, max_points: int = 30) -> str:
    p = _SB.resolve(o_path)
    if not p.is_file():
        return f"[history] 文件不存在: {o_path}"
    t = _clean(_read_o(p))
    n = max(3, int(max_points))

    def _sub(xs):
        if len(xs) <= n:
            return xs
        step = len(xs) / n
        return [xs[int(k * step)] for k in range(n)] + [xs[-1]]

    if str(what).lower() in ("volume", "vol", "temp", "temperature"):
        s = _series_volume(t)
        if not s:
            return "[history] 未找到随时间的状态表（确认是瞬态算例、且有大/小编辑输出）。"
        all_ids = sorted({k for _tt, d in s for k in d})
        if ids:
            use = [x for x in ids if x in all_ids] or all_ids
        else:  # 默认取温度变化幅度最大的几个控制体（最可能是加热段/关键点）
            first = s[0][1]
            swing = {k: max(abs(d.get(k, first.get(k, 0)) - first.get(k, 0)) for _tt, d in s)
                     for k in all_ids}
            use = sorted(all_ids, key=lambda k: -swing.get(k, 0))[:6]
        use = sorted(use)
        ss = _sub(s)
        out = ["[transient_history/volume] 时刻 × 控制体温度 tempf(K)",
               "  time(s) | " + " | ".join(use)]
        for tt, d in ss:
            out.append(f"  {tt:8.3f} | " +
                       " | ".join(f"{d[k]:.1f}" if k in d else "" for k in use))
        return "\n".join(out)

    if str(what).lower() == "state":
        s = _sub(_series_state(t))
        if not s:
            return "[history] 未找到随时间的状态表（确认是瞬态算例、且有大/小编辑输出）。"
        out = ["[transient_history/state] 时刻 × 压力/温度极值",
               "  time(s) | Pmin(Pa) | Pmax(Pa) | Tmin(K) | Tmax(K)"]
        out += [f"  {tt:8.3f} | {v[0]:.4g} | {v[1]:.4g} | {v[2]:.1f} | {v[3]:.1f}"
                for tt, v in s]
        return "\n".join(out)

    s = _series_flow(t)
    if not s:
        return "[history] 未找到随时间变化的接管流量表（确认是瞬态算例、且有大/小编辑输出）。"
    all_ids = sorted({k for _tt, d in s for k in d})
    use = [x for x in (ids or []) if x in all_ids] or \
          sorted(all_ids, key=lambda x: -max(abs(float(d.get(x, 0) or 0)) for _tt, d in s))[:6]
    use = sorted(use)
    ss = _sub(s)
    out = ["[transient_history/flow] 时刻 × 接管质量流量(kg/s)",
           "  time(s) | " + " | ".join(use)]
    for tt, d in ss:
        out.append(f"  {tt:8.3f} | " + " | ".join(str(d.get(k, "")) for k in use))
    return "\n".join(out)

