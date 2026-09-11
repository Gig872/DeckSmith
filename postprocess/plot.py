# -*- coding: utf-8 -*-
"""绘图数据层：把 {id: [(x,y)]} 规整成"图表规格"，供零依赖 Canvas 或（可选）matplotlib 使用。

- chart_spec 纯函数、可测，给出坐标范围与各条线，不含任何绘图库。
- matplotlib_available / render_png：**可选**后端（M5），未装则不影响核心。
"""
from __future__ import annotations

PALETTE = ["#1f77b4", "#d62728", "#2ca02c", "#ff7f0e", "#9467bd",
           "#8c564b", "#17becf", "#e377c2", "#7f7f7f", "#bcbd22"]


def chart_spec(series_map: dict, pad_ratio: float = 0.05) -> dict | None:
    """series_map: {部件号: [(x, y), ...]} → 规格或 None（无数据）。"""
    lines = []
    xs, ys = [], []
    for cid in sorted(series_map):
        pts = list(series_map[cid])
        if not pts:
            continue
        lines.append({"id": cid, "points": pts})
        xs += [p[0] for p in pts]
        ys += [p[1] for p in pts]
    if not xs:
        return None
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    if x1 == x0:
        x1 = x0 + 1.0
    span = (y1 - y0) or (abs(y1) or 1.0)
    pad = span * pad_ratio
    return {"lines": lines, "xrange": (x0, x1), "yrange": (y0 - pad, y1 + pad)}


def matplotlib_available() -> bool:
    try:
        import matplotlib  # noqa: F401
        return True
    except Exception:  # noqa: BLE001
        return False


def render_png(series_map: dict, path, title: str = "", xlabel: str = "time (s)",
               ylabel: str = "") -> str | None:
    """可选：用 matplotlib 出 PNG。未安装 matplotlib 时返回 None（调用方应降级）。"""
    if not matplotlib_available():
        return None
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    # 中文标签：优先选系统里的中文字体，避免 PNG 里出现"方块"（缺字形）
    try:
        matplotlib.rcParams["font.sans-serif"] = [
            "Microsoft YaHei", "SimHei", "SimSun", "Noto Sans CJK SC",
            "WenQuanYi Zen Hei", "Arial Unicode MS", "DejaVu Sans"]
        matplotlib.rcParams["axes.unicode_minus"] = False
    except Exception:  # noqa: BLE001
        pass
    spec = chart_spec(series_map)
    if spec is None:
        return None
    fig, ax = plt.subplots(figsize=(7.2, 4.6), dpi=110)
    for i, ln in enumerate(spec["lines"]):
        xs = [p[0] for p in ln["points"]]
        ys = [p[1] for p in ln["points"]]
        ax.plot(xs, ys, label=ln["id"], color=PALETTE[i % len(PALETTE)], linewidth=1.4)
    ax.set_xlabel(xlabel)
    if ylabel:
        ax.set_ylabel(ylabel)
    if title:
        ax.set_title(title)
    ax.grid(True, alpha=0.3)
    ax.legend(fontsize=8, loc="best")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)
    return str(path)
