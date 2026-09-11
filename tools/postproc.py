# -*- coding: utf-8 -*-
"""后处理工具（2.0）：从 .o 盘点变量、抽取时间序列。

与 `tools/relap5.py` 共享沙箱路径解析。
"""
from __future__ import annotations

from pathlib import Path

from registry import tool
import tools.relap5 as _R
from postprocess import extract as _E
from postprocess import clean as _C
from postprocess import scan as _S
from postprocess import features as _F
from postprocess.plot import matplotlib_available as _mpl_ok, render_png as _render

_SB = _R._SB


@tool("list_output_vars",
      "列出 RELAP5 输出(.o) 里**可提取的变量、部件与编辑时刻**（后处理第一步：先看有什么）。",
      {"o_path": {"type": "string"}}, ["o_path"])
def list_output_vars(o_path: str) -> str:
    p = _SB.resolve(o_path)
    if not p.is_file():
        return f"[postproc] 文件不存在: {o_path}"
    c = _E.catalog(_R._read_o(p))
    ts = c["times"]
    ts_s = f"{len(ts)} 个（{ts[0]:g}…{ts[-1]:g}s）" if ts else "0 个"
    return ("[list_output_vars]\n"
            f"编辑时刻: {ts_s}\n"
            f"控制体变量: {', '.join(c['volume_vars']) or '(无)'}\n"
            f"控制体部件: {', '.join(c['volume_ids']) or '(无)'}\n"
            f"接管变量:   {', '.join(c['junction_vars']) or '(无)'}\n"
            f"接管部件:   {', '.join(c['junction_ids']) or '(无)'}\n"
            "（控制体可抽: pressure/voidf/voidg/tempf/tempg；接管可抽: mass_flow/liq_vel/vap_vel/area）")


@tool("extract_series",
      "抽取某变量的**时间序列**（控制体: pressure/voidf/voidg/tempf/tempg；"
      "接管: mass_flow/liq_vel/vap_vel/area），返回 时刻×部件 表。",
      {"o_path": {"type": "string"},
       "var": {"type": "string", "description": "变量名，见 list_output_vars"},
       "ids": {"type": "array", "description": "只取这些部件号（可省）", "items": {"type": "string"}},
       "max_points": {"type": "integer", "description": "最多给多少时刻，默认 40"}},
      ["o_path", "var"])
def extract_series(o_path: str, var: str, ids=None, max_points: int = 40) -> str:
    p = _SB.resolve(o_path)
    if not p.is_file():
        return f"[postproc] 文件不存在: {o_path}"
    ser = _E.get_series(_R._read_o(p), var, list(ids) if ids else None)
    if not ser:
        return f"[extract_series] 未找到变量 `{var}`（用 list_output_vars 看可用变量）。"
    # 均匀降采样
    n = max(3, int(max_points))
    for cid in ser:
        s = ser[cid]
        if len(s) > n:
            step = len(s) / n
            ser[cid] = [s[int(k * step)] for k in range(n)] + [s[-1]]
    return _E.series_table(ser, var)


@tool("clean_output",
      "清洗 RELAP5 输出(.o)：去控制字符、压空行，写入工作目录 cleaned/，并返回概览统计。",
      {"o_path": {"type": "string"}}, ["o_path"])
def clean_output(o_path: str) -> str:
    p = _SB.resolve(o_path)
    if not p.is_file():
        return f"[postproc] 文件不存在: {o_path}"
    raw = _R._read_o(p)
    out = _SB.root / "cleaned"
    out.mkdir(parents=True, exist_ok=True)
    dst = out / f"{p.stem}_clean.txt"
    dst.write_text(_C.clean_text(raw), encoding="utf-8")
    return (f"[clean_output] 已清洗 → {dst.relative_to(_SB.root)}\n" + _C.summary_text(raw))


@tool("export_series",
      "把某变量的时间序列导出为 CSV/JSON，写到工作目录 exports/。",
      {"o_path": {"type": "string"},
       "var": {"type": "string"},
       "ids": {"type": "array", "description": "只导出这些部件号（可省）", "items": {"type": "string"}},
       "fmt": {"type": "string", "description": "csv（默认）或 json"}},
      ["o_path", "var"])
def export_series(o_path: str, var: str, ids=None, fmt: str = "csv") -> str:
    p = _SB.resolve(o_path)
    if not p.is_file():
        return f"[postproc] 文件不存在: {o_path}"
    ser = _E.get_series(_R._read_o(p), var, list(ids) if ids else None)
    if not ser:
        return f"[export_series] 未找到变量 `{var}`（用 list_output_vars 看可用变量）。"
    out = _SB.root / "exports"
    out.mkdir(parents=True, exist_ok=True)
    if str(fmt).lower() == "json":
        dst = _E.to_json(ser, out / f"{p.stem}_{var}.json", var)
    else:
        dst = _E.to_csv(ser, out / f"{p.stem}_{var}.csv", var)
    n = sum(len(v) for v in ser.values())
    return f"[export_series] 已导出 {len(ser)} 个部件 × {n} 点 → {Path(dst).relative_to(_SB.root)}"


@tool("scan_series",
      "批量扫描趋势：从 batch 的 *_summary.csv + 各工况 .o，抽『某参数 → 某结果量』的趋势，"
      "返回 参数值 × 部件 的表（判断单调性/找拐点/定阈值时用）。",
      {"summary": {"type": "string", "description": "batch 汇总 CSV（工作目录内相对路径，如 batch/xxx_summary.csv）"},
       "x_col": {"type": "string", "description": "作为横轴的自变量列名（可先用 param_columns 看有哪些，如 power）"},
       "var": {"type": "string", "description": "结果变量：pressure/voidf/voidg/tempf/tempg/mass_flow/liq_vel/vap_vel/area"},
       "ids": {"type": "array", "description": "只取这些部件号（可省）", "items": {"type": "string"}},
       "agg": {"type": "string", "description": "last（默认，末值）或 max（最大值）"}},
      ["summary", "x_col", "var"])
def scan_series(summary: str, x_col: str, var: str, ids=None, agg: str = "last") -> str:
    p = _SB.resolve(summary)
    if not p.is_file():
        return f"[postproc] 汇总文件不存在: {summary}"
    try:
        ser = _S.scan_series(p, x_col, var, list(ids) if ids else None,
                             root=_SB.root, agg=str(agg).lower())
    except Exception as e:  # noqa: BLE001
        return f"[scan_series] 读取失败: {e}"
    if not ser:
        cols = _S.param_columns(p)
        return (f"[scan_series] 未得到趋势。可用自变量列: {', '.join(cols) or '(无)'}；"
                "结果变量见 list_output_vars（需各工况 .o 仍在工作目录）。")
    ids_s = sorted(ser)
    xs = sorted({x for v in ser.values() for x, _y in v})
    lines = [f"[scan_series] x={x_col}  var={var}  agg={agg}",
             "  " + x_col + " | " + " | ".join(ids_s)]
    val_of = {cid: dict(ser[cid]) for cid in ids_s}
    for x in xs:
        lines.append(f"  {x:g} | " + " | ".join(
            ("-" if val_of[c].get(x) is None else f"{val_of[c][x]:.5g}") for c in ids_s))
    return "\n".join(lines)


@tool("curve_features",
      "把某变量的时间序列压成**可讲的特征**：趋势（升/降/振荡）、峰/谷(值@时刻)、"
      "末端平台、以及（给 thr 时）阈值穿越时刻。**读图解读前先用它拿数**，再据此讲物理。",
      {"o_path": {"type": "string"},
       "var": {"type": "string", "description": "pressure/voidf/voidg/tempf/tempg/mass_flow/liq_vel/vap_vel/area"},
       "ids": {"type": "array", "description": "只取这些部件号（可省）", "items": {"type": "string"}},
       "thr": {"type": "number", "description": "阈值（可选）：如烧干取 voidg≈0.99、减压取某压力"}},
      ["o_path", "var"])
def curve_features(o_path: str, var: str, ids=None, thr=None) -> str:
    p = _SB.resolve(o_path)
    if not p.is_file():
        return f"[postproc] 文件不存在: {o_path}"
    ser = _E.get_series(_R._read_o(p), var, list(ids) if ids else None)
    if not ser:
        return f"[curve_features] 未找到变量 `{var}`（用 list_output_vars 看可用变量）。"
    feats = _F.curve_features(ser, thr=(float(thr) if thr is not None else None))
    return _F.format_features(feats, var)


@tool("plot_series",
      "为某变量的时间序列**出图**（界面会弹出「结果图」窗口）并给出曲线特征。"
      "装了 matplotlib 则另存 PNG 到 exports/；否则用零依赖 Canvas，不影响解读。"
      "**报告结果时优先用它**：先出图 → 再用返回的特征讲现象与判据。",
      {"o_path": {"type": "string"},
       "var": {"type": "string"},
       "ids": {"type": "array", "description": "只画这些部件号（可省）", "items": {"type": "string"}},
       "thr": {"type": "number", "description": "阈值（可选），用于标注/说明穿越"},
       "png": {"type": "boolean", "description": "是否导出 PNG（默认 true；仅在装了 matplotlib 时生效）"}},
      ["o_path", "var"])
def plot_series(o_path: str, var: str, ids=None, thr=None, png: bool = True) -> str:
    p = _SB.resolve(o_path)
    if not p.is_file():
        return f"[postproc] 文件不存在: {o_path}"
    ser = _E.get_series(_R._read_o(p), var, list(ids) if ids else None)
    if not ser:
        return f"[plot_series] 未找到变量 `{var}`（用 list_output_vars 看可用变量）。"
    feats = _F.curve_features(ser, thr=(float(thr) if thr is not None else None))
    notes = [f"[plot_series] 已为 {var} 出图（界面「结果图」窗口）"]
    if png and _mpl_ok():
        out = _SB.root / "exports"
        out.mkdir(parents=True, exist_ok=True)
        dst = out / f"{p.stem}_{var}.png"
        r = _render(ser, dst, title=var, ylabel=var)
        notes.append(f"PNG → {Path(r).relative_to(_SB.root)}" if r
                     else "PNG 导出失败（已保留 Canvas 显示）")
    elif png:
        notes.append("未装 matplotlib：用零依赖 Canvas 显示（需要精细 PNG 可在结果图窗口『启用 matplotlib』）")
    return "\n".join(notes) + "\n" + _F.format_features(feats, var)
