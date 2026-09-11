# -*- coding: utf-8 -*-
"""批量扫描结果：从批量的 summary.csv + 各工况 .o 抽"参数 → 结果"趋势。

用途：batch_sim 跑完一批后，画出"某自变量 × 某结果量"的趋势线。
"""
from __future__ import annotations

import csv
from pathlib import Path

from .extract import get_series


def read_summary(csv_path: str | Path) -> tuple[list[str], list[dict]]:
    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        r = csv.DictReader(f)
        return list(r.fieldnames or []), list(r)


def param_columns(csv_path: str | Path) -> list[str]:
    """可作为 x 轴的列：非结果列、且整列可转 float。"""
    cols, rows = read_summary(csv_path)
    _skip = {"正常结束", "质量误差", "压力范围", "温度范围", "voidg_max", "烧干?", "错误(首条)", "o"}
    out = []
    for c in cols:
        if c in _skip:
            continue
        vals = []
        for row in rows:
            try:
                vals.append(float(row.get(c)))
            except (TypeError, ValueError):
                vals = []
                break
        if vals:
            out.append(c)
    return out


def scan_series(csv_path: str | Path, x_col: str, var: str,
                ids: list[str] | None = None, root: str | Path = ".",
                agg: str = "last") -> dict:
    """返回 {部件号: [(x, 结果值), ...]}。

    x 取自 summary 的 `x_col` 列；结果值取自每个工况 `.o` 里 `var` 的
    **末值(agg='last')或最大值(agg='max')**。
    """
    _cols, rows = read_summary(csv_path)
    root = Path(root)
    out: dict[str, list] = {}
    for row in rows:
        try:
            x = float(row.get(x_col))
        except (TypeError, ValueError):
            continue
        o = row.get("o") or ""
        if not o:
            continue
        p = Path(o)
        if not p.is_absolute():
            p = root / o
        if not p.is_file():
            continue
        ser = get_series(p.read_text(encoding="utf-8", errors="replace"), var, ids)
        for cid, pts in ser.items():
            if not pts:
                continue
            y = (max(v for _t, v in pts) if agg == "max" else pts[-1][1])
            out.setdefault(cid, []).append((x, y))
    for cid in out:
        out[cid].sort(key=lambda pv: pv[0])
    return out
