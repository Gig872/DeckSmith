# -*- coding: utf-8 -*-
"""从解析结果抽取时间序列，并格式化/导出。"""
from __future__ import annotations

import csv
import json
from pathlib import Path

from .parse import parse, output_times, VOL_VARS, JUN_VARS

_ALL_VOL = set(VOL_VARS)
_ALL_JUN = set(JUN_VARS)


def catalog(text: str) -> dict:
    """盘点这份 .o 里可提取什么：变量、部件、时刻。"""
    vol, jun = parse(text)
    vol_vars = sorted({v for d in vol.values() for v in d})
    jun_vars = sorted({v for d in jun.values() for v in d})
    return {
        "times": output_times(vol, jun),
        "volume_ids": sorted(vol),
        "junction_ids": sorted(jun),
        "volume_vars": vol_vars,
        "junction_vars": jun_vars,
    }


def get_series(text: str, var: str, ids: list[str] | None = None) -> dict:
    """抽某变量的时间序列：{部件号: [(t, val), ...]}。var 见 VOL_VARS / JUN_VARS。"""
    vol, jun = parse(text)
    if var in _ALL_VOL:
        src = vol
    elif var in _ALL_JUN:
        src = jun
    else:
        return {}
    want = set(ids) if ids else None
    out = {}
    for cid, d in src.items():
        if want is not None and cid not in want:
            continue
        if var in d:
            out[cid] = d[var]
    return out


def series_table(series: dict, var: str) -> str:
    """把 {id: [(t,val)]} 渲染成文本表（时刻 × 各部件）。"""
    if not series:
        return f"(未找到变量 {var} 的数据)"
    # 以第一个序列的时刻为基准（各序列时刻应一致）
    ids = sorted(series)
    times = [t for t, _v in series[ids[0]]]
    val_of = {cid: {t: v for t, v in series[cid]} for cid in ids}
    lines = [f"[{var}] 时刻 × 部件",
             "  time(s) | " + " | ".join(ids)]
    for t in times:
        lines.append(f"  {t:8.3f} | " +
                     " | ".join(f"{val_of[c].get(t, float('nan')):.5g}" for c in ids))
    return "\n".join(lines)


def to_csv(series: dict, path: str | Path, var: str = "") -> str:
    ids = sorted(series)
    if not ids:
        return ""
    times = [t for t, _v in series[ids[0]]]
    val_of = {cid: {t: v for t, v in series[cid]} for cid in ids}
    p = Path(path)
    with open(p, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.writer(f)
        w.writerow(["time_s"] + ids)
        for t in times:
            w.writerow([t] + [val_of[c].get(t, "") for c in ids])
    return str(p)


def to_json(series: dict, path: str | Path, var: str = "") -> str:
    p = Path(path)
    data = {"var": var, "series": {cid: series[cid] for cid in sorted(series)}}
    p.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return str(p)
