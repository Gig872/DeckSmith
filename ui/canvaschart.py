# -*- coding: utf-8 -*-
"""零依赖 tk.Canvas 折线绘制：结果图（时间序列）与批量扫描图（参数趋势）共用。"""
from __future__ import annotations

from postprocess.plot import PALETTE


def draw_chart(canvas, spec, xlabel: str = "time (s)", ylabel: str = "",
               placeholder: str = "无数据（选个变量点『绘制』）"):
    """把 chart_spec 的 lines 画到 canvas 上；spec 为空则画占位提示。"""
    c = canvas
    c.delete("all")
    if not spec or not spec.get("lines"):
        c.create_text(20, 20, anchor="nw", text=placeholder, fill="#888")
        return
    W = c.winfo_width() or 820
    H = c.winfo_height() or 500
    L, Rm, T, B = 78, 150, 40, 46
    pw, ph = W - L - Rm, H - T - B
    x0, x1 = spec["xrange"]
    y0, y1 = spec["yrange"]
    if x1 == x0:
        x1 = x0 + 1
    if y1 == y0:
        y1 = y0 + 1

    def px(x):
        return L + (x - x0) / (x1 - x0) * pw

    def py(y):
        return T + (y1 - y) / (y1 - y0) * ph

    # 网格 + 刻度
    for i in range(6):
        xx = L + pw * i / 5
        c.create_line(xx, T, xx, T + ph, fill="#eee")
        c.create_text(xx, T + ph + 14, text=f"{x0 + (x1 - x0) * i / 5:.3g}", fill="#555", font=("", 8))
    for i in range(5):
        yy = T + ph * i / 4
        c.create_line(L, yy, L + pw, yy, fill="#eee")
        c.create_text(L - 8, yy, anchor="e", text=f"{y1 - (y1 - y0) * i / 4:.4g}", fill="#555", font=("", 8))
    c.create_rectangle(L, T, L + pw, T + ph, outline="#999")
    c.create_text(L + pw / 2, H - 12, text=xlabel, fill="#333")
    if ylabel:
        c.create_text(14, T + ph / 2, text=ylabel, angle=90, fill="#333", font=("", 9, "bold"))

    # 曲线
    for i, ln in enumerate(spec["lines"]):
        pts = ln["points"]
        if not pts:
            continue
        color = PALETTE[i % len(PALETTE)]
        if len(pts) == 1:
            c.create_oval(px(pts[0][0]) - 2, py(pts[0][1]) - 2,
                          px(pts[0][0]) + 2, py(pts[0][1]) + 2, fill=color)
        else:
            coords = []
            for (xx, yy) in pts:
                coords += [px(xx), py(yy)]
            c.create_line(*coords, fill=color, width=1.6)
        # 图例
        ly = T + 4 + i * 16
        c.create_line(L + pw + 12, ly, L + pw + 30, ly, fill=color, width=2)
        c.create_text(L + pw + 34, ly, anchor="w", text=ln["id"], fill="#333", font=("", 8))
