# -*- coding: utf-8 -*-
"""关键标量的聚合口径（refrun / runner 共用）。

agg 写法为 `时间口径:跨部件口径`：
  时间口径：last（末态，**稳态题用**）· peak（全程最大绝对值，**瞬态题用**）· trough（全程最小值）
  跨部件口径：max · min · maxabs
未写冒号时默认 **last:...**（即按稳态处理）——稳态题只写 `max/min/maxabs` 即为末态口径，
避免被启动瞬态尖峰污染。
"""
from __future__ import annotations

from postprocess.extract import get_series


def _time_agg(pts, kind: str) -> float:
    ys = [y for _t, y in pts]
    if kind == "peak":
        return max(ys, key=abs)
    if kind == "trough":
        return min(ys)
    return ys[-1]          # last（默认）


def scalars(text: str, key_outputs: list) -> dict:
    out = {}
    for spec in key_outputs:
        var = spec["var"]
        agg = str(spec.get("agg", "max"))
        tkind, _, ckind = agg.partition(":")
        if not ckind:
            tkind, ckind = "last", ("min" if agg == "min" else
                                    ("maxabs" if agg == "maxabs" else "max"))
        ser = get_series(text, var)
        picks = [_time_agg(pts, tkind) for _cid, pts in ser.items() if pts]
        key = f"{var}:{agg}"
        if not picks:
            out[key] = None
        elif ckind == "min":
            out[key] = min(picks)
        elif ckind == "maxabs":
            out[key] = max(picks, key=abs)
        else:
            out[key] = max(picks)
    return out


def compare(scal: dict, exp: dict, key_outputs: list) -> bool:
    """行为等价：所有关键标量在容差内一致。"""
    if not exp:
        return False
    for spec in key_outputs:
        k = f'{spec["var"]}:{spec.get("agg", "max")}'
        a, b = scal.get(k), exp.get(k)
        if a is None or b is None:
            return False
        tol, mode = spec.get("tol", 0.05), spec.get("mode", "rel")
        if mode == "rel":
            if abs(a - b) / (abs(b) or 1.0) > tol:
                return False
        else:
            if abs(a - b) > tol:
                return False
    return True
