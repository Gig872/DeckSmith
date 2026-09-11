# -*- coding: utf-8 -*-
"""曲线特征（“读图”的数据底座）：把一条时间序列压成可讲的特征点。

纯函数、可测。给 agent 用：让它**基于数值特征**讲趋势/拐点/峰值/平台/阈值穿越，
而不是凭空形容曲线。配合 skill 60（读图解读）。
"""
from __future__ import annotations


def _trend(ts, vs, span: float) -> str:
    n = len(vs)
    delta = vs[-1] - vs[0]
    net = delta / span if span else 0.0
    # 方向翻转次数（振荡判据）
    diffs = [vs[i + 1] - vs[i] for i in range(n - 1)]
    flips = sum(1 for i in range(1, len(diffs))
                if diffs[i - 1] * diffs[i] < 0 and abs(diffs[i]) > 1e-12)
    if span <= 0:
        return "平稳"
    if flips >= 4 and abs(net) < 0.4:
        return "振荡"
    if net >= 0.5:
        return "总体上升"
    if net <= -0.5:
        return "总体下降"
    imin = vs.index(min(vs))
    imax = vs.index(max(vs))
    if imin < imax:
        return "先降后升"
    if imax < imin:
        return "先升后降"
    return "波动"


def curve_features(series_map: dict, thr: float | None = None,
                   tol: float = 0.02) -> list[dict]:
    """series_map: {部件号: [(t, v), ...]} → 每部件的特征 dict 列表（按部件号排序）。"""
    out = []
    for cid in sorted(series_map):
        pts = list(series_map[cid])
        if not pts:
            continue
        ts = [p[0] for p in pts]
        vs = [p[1] for p in pts]
        n = len(vs)
        vmin, vmax = min(vs), max(vs)
        imin, imax = vs.index(vmin), vs.index(vmax)
        span = vmax - vmin
        d = {
            "id": cid, "n": n, "t0": ts[0], "t1": ts[-1],
            "first": vs[0], "last": vs[-1], "delta": vs[-1] - vs[0],
            "min": vmin, "t_min": ts[imin], "max": vmax, "t_max": ts[imax],
            "span": span, "trend": _trend(ts, vs, span),
            "plateau": None, "plateau_from": None,
            "cross": None,
        }
        # 末端平台：最后一段（≥3 点）波动很小
        k = max(3, n // 10)
        if n >= k:
            tail = vs[-k:]
            rng = max(tail) - min(tail)
            ref = span or abs(vmax) or 1.0
            if rng <= tol * ref:
                d["plateau"] = sum(tail) / len(tail)
                d["plateau_from"] = ts[-k]
        # 阈值穿越（可给"烧干 voidg→1""压力降到 X"等判据）
        if thr is not None:
            for i in range(1, n):
                a, b = vs[i - 1] - thr, vs[i] - thr
                if a == 0 or a * b < 0:
                    d["cross"] = {"thr": thr, "t": ts[i],
                                  "dir": "上穿" if b > 0 else "下穿",
                                  "last_side": "高于" if vs[-1] >= thr else "低于"}
                    break
        out.append(d)
    return out


def format_features(feats: list[dict], var: str = "") -> str:
    """把特征渲染成人读文本（供工具返回给模型）。"""
    if not feats:
        return "(无曲线数据)"
    lines = [f"[曲线特征] {var}（t∈[t0,t1]；趋势/峰值/平台/穿越）"]
    for f in feats:
        head = (f"  · {f['id']}: n={f['n']}, t={f['t0']:g}→{f['t1']:g}s, "
                f"趋势={f['trend']}")
        lines.append(head)
        lines.append(f"      起={f['first']:.5g} 末={f['last']:.5g}（Δ={f['delta']:+.3g}）")
        lines.append(f"      峰={f['max']:.5g}@t={f['t_max']:g}s  "
                     f"谷={f['min']:.5g}@t={f['t_min']:g}s")
        if f["plateau"] is not None:
            lines.append(f"      末端趋稳≈{f['plateau']:.5g}（自 t={f['plateau_from']:g}s 起）")
        if f["cross"]:
            c = f["cross"]
            lines.append(f"      {c['dir']} {c['thr']:g} @t={c['t']:g}s；末值{c['last_side']}阈值")
    return "\n".join(lines)
