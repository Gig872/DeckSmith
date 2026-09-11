# -*- coding: utf-8 -*-
"""水的独立物性估算（供“自主评估”比对仿真读数用）。

**刻意保持简单、可复现，并明确标注适用范围**——它的用途是**量级/一致性核对**
（饱和温度、过冷/过热、能量平衡），不是替代物性表。纯函数、可测。

- `sat_temp_K(p)`：IAPWS-IF97 第 4 区**显式**饱和温度式（0.000611–22.064 MPa，准）。
- `cp_liquid(t)`：饱和液态水定压比热，查表线性插值（0–340 ℃，约 ±5–10%）。
- `h_fg(p)`：汽化潜热，Watson 关联（以 100 ℃、2256.4 kJ/kg 为参考）。
"""
from __future__ import annotations

import math

# IAPWS-IF97 region 4 系数
_N = (0.11670521452767e4, -0.72421316703206e6, -0.17073846940092e2,
      0.12020824702470e5, -0.32325550322333e7, 0.14915108613530e2,
      -0.48232657361591e4, 0.40511340542057e6, -0.23855557567849,
      0.65017534844798e3)

_TC = 647.096          # 临界温度 K
_PC = 22.064e6         # 临界压力 Pa
_P_TRIPLE = 611.657    # 三相点压力 Pa

# 饱和液态水 cp (kJ/kg·K) vs 温度(℃)——查表插值
_CP_T = (0.0, 20.0, 50.0, 100.0, 150.0, 200.0, 250.0, 300.0, 340.0)
_CP_V = (4.217, 4.182, 4.181, 4.216, 4.310, 4.490, 4.860, 5.750, 7.20)


def sat_temp_K(p_pa: float) -> float:
    """饱和温度 [K]；超范围/非法输入返回 nan。"""
    try:
        p = float(p_pa)
    except (TypeError, ValueError):
        return float("nan")
    if not (p > 0) or p < _P_TRIPLE * 0.999 or p > _PC:
        return float("nan")
    p = p / 1e6      # MPa
    beta = p ** 0.25
    e = beta * beta + _N[2] * beta + _N[5]
    f = _N[0] * beta * beta + _N[3] * beta + _N[6]
    g = _N[1] * beta * beta + _N[4] * beta + _N[7]
    disc = f * f - 4 * e * g
    if disc < 0 or (-f - math.sqrt(disc)) == 0:
        return float("nan")
    d = 2 * g / (-f - math.sqrt(disc))
    val = (d + _N[9]) ** 2 - 4 * (_N[8] + _N[9] * d)
    if val < 0:
        return float("nan")
    return (_N[9] + d - math.sqrt(val)) / 2


def cp_liquid(t_k: float) -> float:
    """饱和液态水定压比热 [kJ/kg·K]（0–340 ℃，查表插值）。"""
    try:
        tc = float(t_k) - 273.15
    except (TypeError, ValueError):
        return float("nan")
    if tc <= _CP_T[0]:
        return _CP_V[0]
    if tc >= _CP_T[-1]:
        return _CP_V[-1]
    for i in range(1, len(_CP_T)):
        if tc <= _CP_T[i]:
            t0, t1 = _CP_T[i - 1], _CP_T[i]
            v0, v1 = _CP_V[i - 1], _CP_V[i]
            return v0 + (v1 - v0) * (tc - t0) / (t1 - t0)
    return _CP_V[-1]


def h_fg(p_pa: float) -> float:
    """汽化潜热 [kJ/kg]（Watson 关联，以 100 ℃、2256.4 kJ/kg 为参考）。"""
    ts = sat_temp_K(p_pa)
    if math.isnan(ts) or ts >= _TC:
        return 0.0
    return 2256.4 * ((_TC - ts) / (_TC - 373.15)) ** 0.38


def notes() -> str:
    return ("估算口径：饱和温度用 IAPWS-IF97 第 4 区显式式（准）；cp 查表插值（0–340℃，±5–10%）；"
            "潜热用 Watson 关联。用于**量级/一致性**核对，非替代物性表。")
