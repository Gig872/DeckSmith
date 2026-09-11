# -*- coding: utf-8 -*-
"""结果图窗口：独立 Toplevel，零依赖 tk.Canvas 折线（可多开）。

- **变量 / 部件均可多选、任意组合**（每个组合一条线）；
- 变量名显示中文（`voidg（空泡份额）`）；
- 可选「归一化(0–1)」把量纲不同的多条线画在一起。
数据来自 `postprocess/`（解析 + 抽序列）。
"""
from __future__ import annotations

import csv
import tkinter as tk
from pathlib import Path
from tkinter import ttk

import tools.relap5 as _R
from postprocess import extract as _E
from postprocess.plot import chart_spec, matplotlib_available, render_png
from .canvaschart import draw_chart
from .constants import var_label


class PlotWindow:
    def __init__(self, root: tk.Tk, o_rel: str, ensure_cb=None, var: str = ""):
        self.o_rel = o_rel
        self._want_var = var or ""
        self._ensure = ensure_cb or matplotlib_available    # 探库→（可由外层触发）自动安装
        self._spec = None
        self._var_raw: list[str] = []
        self._ids_raw: list[str] = []

        self.win = tk.Toplevel(root)
        self.win.title(f"结果图 —— {o_rel}")
        self.win.geometry("980x640")

        # ---- 左侧：变量 / 部件多选 ----
        left = ttk.Frame(self.win)
        left.pack(side="left", fill="y", padx=(8, 4), pady=6)
        ttk.Label(left, text="变量（可多选）").pack(anchor="w")
        self.lb_var = tk.Listbox(left, selectmode="extended", exportselection=False,
                                 width=24, height=8)
        self.lb_var.pack(fill="x")
        ttk.Label(left, text="部件（可多选）").pack(anchor="w", pady=(8, 0))
        idbox = ttk.Frame(left)
        idbox.pack(fill="both", expand=True)
        self.lb_ids = tk.Listbox(idbox, selectmode="extended", exportselection=False,
                                 width=24, height=14)
        sb = ttk.Scrollbar(idbox, orient="vertical", command=self.lb_ids.yview)
        self.lb_ids.configure(yscrollcommand=sb.set)
        self.lb_ids.pack(side="left", fill="both", expand=True)
        sb.pack(side="left", fill="y")
        self.norm = tk.BooleanVar(value=False)
        ttk.Checkbutton(left, text="归一化(0–1)（量纲不同时勾选）", variable=self.norm).pack(anchor="w", pady=(6, 0))
        rowb = ttk.Frame(left)
        rowb.pack(fill="x", pady=6)
        ttk.Button(rowb, text="全选变量", command=lambda: self._select(listbox=self.lb_var)).pack(side="left")
        ttk.Button(rowb, text="全选部件", command=lambda: self._select(listbox=self.lb_ids)).pack(side="left", padx=2)
        ttk.Button(rowb, text="清空", command=self._clear_sel).pack(side="left")

        # ---- 右侧：操作 + 画布 ----
        right = ttk.Frame(self.win)
        right.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=6)
        top = ttk.Frame(right)
        top.pack(fill="x")
        ttk.Button(top, text="绘制", command=self._draw).pack(side="left")
        ttk.Button(top, text="导出 CSV", command=self._export_csv).pack(side="left", padx=2)
        ttk.Button(top, text="导出图片", command=self._export_png).pack(side="left", padx=2)
        self.btn_mpl = ttk.Button(top, text="启用 matplotlib", command=self._enable_mpl)
        self.btn_mpl.pack(side="left", padx=2)
        self.lbl = ttk.Label(top, text="", foreground="#666")
        self.lbl.pack(side="right")

        self.canvas = tk.Canvas(right, background="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, pady=(6, 0))
        self.canvas.bind("<Configure>", lambda _e: self._render())

        self._load_catalog()

    # ---- 数据 ----
    def _text(self) -> str:
        p = _R._SB.resolve(self.o_rel)
        return _R._read_o(p) if p.is_file() else ""

    def _load_catalog(self):
        cat = _E.catalog(self._text())
        self._var_raw = cat["volume_vars"] + cat["junction_vars"]
        self._ids_raw = sorted(set(cat["volume_ids"]) | set(cat["junction_ids"]))
        self.lb_var.delete(0, "end")
        for v in self._var_raw:
            self.lb_var.insert("end", var_label(v))
        self.lb_ids.delete(0, "end")
        for i in self._ids_raw:
            self.lb_ids.insert("end", i)
        # 预选变量：外层指定优先，否则 tempf / 第一个
        want = self._want_var if self._want_var in self._var_raw else (
            "tempf" if "tempf" in self._var_raw else (self._var_raw[0] if self._var_raw else ""))
        if want in self._var_raw:
            self.lb_var.selection_set(self._var_raw.index(want))
        # 预选部件：不多时全选，多了留空让用户点
        if 0 < len(self._ids_raw) <= 12:
            self.lb_ids.selection_set(0, "end")
        self._draw()

    def _select(self, listbox=None):
        if self.lb_var.size():
            self.lb_var.selection_set(0, "end")
        if self.lb_ids.size():
            self.lb_ids.selection_set(0, "end")

    def _clear_sel(self):
        self.lb_var.selection_clear(0, "end")
        self.lb_ids.selection_clear(0, "end")

    def _picked(self):
        vs = [self._var_raw[i] for i in self.lb_var.curselection()]
        ids = [self._ids_raw[i] for i in self.lb_ids.curselection()]
        return vs, ids

    def _series_map(self):
        """{显示名: [(t,v)]}；每个 (变量 × 部件) 组合一条线。"""
        text = self._text()
        vs, ids = self._picked()
        out = {}
        for v in vs:
            ser = _E.get_series(text, v, ids or None)
            for cid, pts in ser.items():
                out[f"{cid} · {var_label(v)}"] = list(pts)
        if self.norm.get():
            for k, pts in out.items():
                ys = [y for _t, y in pts]
                lo, hi = min(ys), max(ys)
                rng = (hi - lo) or 1.0
                out[k] = [(t, (y - lo) / rng) for t, y in pts]
        return out

    # ---- 绘制 ----
    def _draw(self):
        vs, ids = self._picked()
        if not vs or not ids:
            self.lbl.configure(text="请至少选 1 个变量和 1 个部件")
            self._spec = None
            self._render()
            return
        ser = self._series_map()
        if not ser:
            self.lbl.configure(text="所选变量/部件无数据")
        spec = chart_spec(ser)
        self._spec = (spec, ser, "、".join(vs))
        self._render()

    def _render(self):
        spec = self._spec[0] if self._spec else None
        ylab = "归一化值(0–1)" if self.norm.get() else "值"
        draw_chart(self.canvas, spec, xlabel="time (s)", ylabel=ylab)
        if spec:
            mode = "matplotlib 可用" if matplotlib_available() else "Canvas 模式"
            self.lbl.configure(text=f"{len(spec['lines'])} 条 · {mode}")
        self._sync_mpl_btn()

    def _sync_mpl_btn(self):
        try:
            self.btn_mpl.configure(state=("disabled" if matplotlib_available() else "normal"))
        except tk.TclError:
            pass

    def _enable_mpl(self):
        if self._ensure():
            self.lbl.configure(text="matplotlib 已就绪，可『导出图片』（PNG）")
        self._sync_mpl_btn()

    # ---- 导出 ----
    def _export_csv(self):
        if not self._spec or not self._spec[1]:
            self.lbl.configure(text="无可导出数据")
            return
        ser = self._spec[1]
        out = Path(_R._SB.root) / "exports"
        out.mkdir(parents=True, exist_ok=True)
        dst = out / f"{Path(self.o_rel).stem}_series.csv"
        ts = sorted({t for pts in ser.values() for t, _y in pts})
        val = {k: dict(pts) for k, pts in ser.items()}
        keys = sorted(ser)
        with open(dst, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow(["time_s"] + keys)
            for t in ts:
                w.writerow([t] + [val[k].get(t, "") for k in keys])
        self.lbl.configure(text=f"已导出 {dst.name}")

    def _export_png(self):
        if not self._spec or not self._spec[1]:
            self.lbl.configure(text="无可导出数据")
            return
        ser, title = self._spec[1], self._spec[2]
        out = Path(_R._SB.root) / "exports"
        out.mkdir(parents=True, exist_ok=True)
        dst = out / f"{Path(self.o_rel).stem}_series.png"
        if not matplotlib_available() and not self._ensure():
            self.lbl.configure(text="未启用 matplotlib，PNG 未导出（Canvas 显示不受影响）")
            self._sync_mpl_btn()
            return
        p = render_png(ser, dst, title=title, ylabel=("归一化值" if self.norm.get() else "值"))
        self.lbl.configure(text=(f"已导出 {dst.name}" if p else "matplotlib 出图失败（已保留 Canvas 显示）"))
        self._sync_mpl_btn()


class PlotWindowMixin:
    @staticmethod
    def _norm_o(rel: str) -> str:
        rel = str(rel or "").replace("\\", "/")
        return rel[len("workspace/"):] if rel.startswith("workspace/") else rel

    def _open_plot_window(self):
        rel = self._last_o()
        if not rel:
            self._log("agent", "还没有可画的运行结果（先真跑一个算例，再打开结果图）。")
            return
        self._plot_wins.append(PlotWindow(self.root, rel, ensure_cb=self._ensure_plot_backend))
        self._raise_window(self._plot_wins[-1].win)

    def _open_plot_window_for(self, o_rel: str, var: str = ""):
        """agent 调 plot_series/curve_features 时自动开窗（视图菜单可关）。"""
        rel = self._norm_o(o_rel)
        if not rel:
            return
        try:
            w = PlotWindow(self.root, rel, ensure_cb=self._ensure_plot_backend, var=var)
            self._plot_wins.append(w)
            self._raise_window(w.win)
        except Exception as e:  # noqa: BLE001
            self._log("agent", f"（出图窗口打开失败：{type(e).__name__}: {e}）")

    @staticmethod
    def _raise_window(win: tk.Toplevel):
        """让新窗口弹到最前（否则可能被主窗盖住，看着像"没弹出"）。"""
        try:
            win.deiconify()
            win.lift()
            win.attributes("-topmost", True)
            win.after(500, lambda: win.winfo_exists() and win.attributes("-topmost", False))
            win.focus_force()
        except tk.TclError:
            pass
