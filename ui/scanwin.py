# -*- coding: utf-8 -*-
"""批量扫描图窗口：独立 Toplevel，画『参数 → 结果量』趋势（可多开）。

- **变量 / 部件均可多选、任意组合**（每个组合一条趋势线）；
- 变量名显示中文；可选「归一化(0–1)」。
数据来自 batch 的 *_summary.csv + 各工况 .o（`postprocess/scan.py`）。
复用零依赖 tk.Canvas 折线（ui/canvaschart.py）。
"""
from __future__ import annotations

import csv
from pathlib import Path
import tkinter as tk
from tkinter import ttk

import tools.relap5 as _R
from postprocess import extract as _E
from postprocess import scan as _S
from postprocess.parse import VOL_VARS, JUN_VARS
from postprocess.plot import chart_spec, matplotlib_available, render_png
from .canvaschart import draw_chart
from .constants import var_label

_AGG = {"末值 (last)": "last", "最大值 (max)": "max"}


class ScanWindow:
    def __init__(self, root: tk.Tk, workspace: str | None = None, ensure_cb=None):
        self.root_dir = Path(workspace or _R._SB.root)
        self.batch_dir = self.root_dir / "batch"
        self._ensure = ensure_cb or matplotlib_available
        self._spec = None
        self._var_raw: list[str] = []
        self._ids_raw: list[str] = []

        self.win = tk.Toplevel(root)
        self.win.title("批量扫描趋势图")
        self.win.geometry("1040x660")

        # ---- 顶部：汇总 / 横轴 / 聚合 ----
        top = ttk.Frame(self.win)
        top.pack(fill="x", padx=8, pady=6)
        ttk.Label(top, text="汇总").pack(side="left")
        self.sum = tk.StringVar()
        self.cb_sum = ttk.Combobox(top, textvariable=self.sum, width=26, state="readonly")
        self.cb_sum.pack(side="left", padx=4)
        ttk.Label(top, text="横轴").pack(side="left", padx=(8, 0))
        self.xcol = tk.StringVar()
        self.cb_x = ttk.Combobox(top, textvariable=self.xcol, width=10, state="readonly")
        self.cb_x.pack(side="left", padx=4)
        ttk.Label(top, text="聚合").pack(side="left", padx=(8, 0))
        self.agg = tk.StringVar(value="末值 (last)")
        ttk.Combobox(top, textvariable=self.agg, width=11, state="readonly",
                     values=list(_AGG)).pack(side="left", padx=4)
        ttk.Button(top, text="绘制", command=self._draw).pack(side="left", padx=8)
        ttk.Button(top, text="导出 CSV", command=self._export_csv).pack(side="left", padx=2)
        ttk.Button(top, text="导出图片", command=self._export_png).pack(side="left", padx=2)
        self.btn_mpl = ttk.Button(top, text="启用 matplotlib", command=self._enable_mpl)
        self.btn_mpl.pack(side="left", padx=2)

        # ---- 左侧：变量 / 部件多选 ----
        left = ttk.Frame(self.win)
        left.pack(side="left", fill="y", padx=(8, 4), pady=(0, 6))
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
        ttk.Button(rowb, text="全选变量", command=lambda: self.lb_var.selection_set(0, "end")).pack(side="left")
        ttk.Button(rowb, text="全选部件", command=lambda: self.lb_ids.selection_set(0, "end")).pack(side="left", padx=2)
        ttk.Button(rowb, text="清空", command=self._clear_sel).pack(side="left")

        # ---- 右侧：画布 ----
        right = ttk.Frame(self.win)
        right.pack(side="left", fill="both", expand=True, padx=(0, 8), pady=(0, 6))
        self.lbl = ttk.Label(right, text="", foreground="#666")
        self.lbl.pack(anchor="w")
        self.canvas = tk.Canvas(right, background="white", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, pady=(4, 0))
        self.canvas.bind("<Configure>", lambda _e: self._render())

        self.cb_sum.bind("<<ComboboxSelected>>", lambda _e: self._load_summary())
        self._load_summaries()

    # ---------- 载入 ----------
    def _summaries(self) -> list[str]:
        if not self.batch_dir.is_dir():
            return []
        return sorted(p.name for p in self.batch_dir.glob("*_summary.csv"))

    def _load_summaries(self):
        names = self._summaries()
        self.cb_sum.configure(values=names)
        if names:
            self.sum.set(names[-1])          # 默认最近一次
            self._load_summary()
        else:
            self.lbl.configure(text="workspace/batch/ 下还没有 *_summary.csv（先跑一次 batch_sim）")

    def _load_summary(self):
        p = self.batch_dir / self.sum.get()
        if not p.is_file():
            return
        cols = _S.param_columns(p)
        self.cb_x.configure(values=cols)
        if cols:
            self.xcol.set(cols[0])
        o = self._first_o(p)
        cat = _E.catalog(self._read_o(o)) if o else {}
        self._var_raw = (cat.get("volume_vars", []) + cat.get("junction_vars", [])) \
            or list(VOL_VARS) + list(JUN_VARS)
        self._ids_raw = sorted(set(cat.get("volume_ids", [])) | set(cat.get("junction_ids", [])))
        self.lb_var.delete(0, "end")
        for v in self._var_raw:
            self.lb_var.insert("end", var_label(v))
        self.lb_ids.delete(0, "end")
        for i in self._ids_raw:
            self.lb_ids.insert("end", i)
        want = "voidg" if "voidg" in self._var_raw else (self._var_raw[0] if self._var_raw else "")
        if want in self._var_raw:
            self.lb_var.selection_set(self._var_raw.index(want))
        if 0 < len(self._ids_raw) <= 12:
            self.lb_ids.selection_set(0, "end")
        self._draw()

    def _first_o(self, summary: Path):
        _cols, rows = _S.read_summary(summary)
        for r in rows:
            o = (r.get("o") or "").replace("\\", "/")
            if not o:
                continue
            q = Path(o)
            if not q.is_absolute():
                q = self.root_dir / o
            if q.is_file():
                return q
        return None

    @staticmethod
    def _read_o(p: Path) -> str:
        return p.read_text(encoding="utf-8", errors="replace")

    def _clear_sel(self):
        self.lb_var.selection_clear(0, "end")
        self.lb_ids.selection_clear(0, "end")

    def _picked(self):
        vs = [self._var_raw[i] for i in self.lb_var.curselection()]
        ids = [self._ids_raw[i] for i in self.lb_ids.curselection()]
        return vs, ids

    # ---------- 绘制 ----------
    def _series_map(self):
        p = self.batch_dir / self.sum.get()
        vs, ids = self._picked()
        out = {}
        for v in vs:
            ser = _S.scan_series(p, self.xcol.get(), v, ids or None,
                                 root=self.root_dir, agg=_AGG[self.agg.get()])
            for cid, pts in ser.items():
                out[f"{cid} · {var_label(v)}"] = list(pts)
        if self.norm.get():
            for k, pts in out.items():
                ys = [y for _x, y in pts]
                lo, hi = min(ys), max(ys)
                rng = (hi - lo) or 1.0
                out[k] = [(x, (y - lo) / rng) for x, y in pts]
        return out

    def _draw(self):
        p = self.batch_dir / self.sum.get()
        if not p.is_file():
            self.lbl.configure(text="先选一个汇总文件")
            return
        vs, ids = self._picked()
        if not vs or not ids:
            self.lbl.configure(text="请至少选 1 个变量和 1 个部件")
            self._spec = None
            self._render()
            return
        ser = self._series_map()
        if not ser:
            self.lbl.configure(text="无趋势数据（工况 .o 是否还在？）")
        spec = chart_spec(ser)
        self._spec = (spec, ser, "、".join(vs))
        self._render()

    def _render(self):
        spec = self._spec[0] if self._spec else None
        xcol = self.xcol.get()
        ylab = "归一化值(0–1)" if self.norm.get() else "值"
        draw_chart(self.canvas, spec, xlabel=xcol, ylabel=ylab,
                   placeholder="选好参数后点『绘制』")
        if spec:
            self.lbl.configure(text=f"{len(spec['lines'])} 条 · x={xcol} · agg={_AGG[self.agg.get()]}")
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

    # ---------- 导出 ----------
    def _export_csv(self):
        if not self._spec or not self._spec[1]:
            self.lbl.configure(text="无可导出数据")
            return
        ser = self._spec[1]
        xcol = self.xcol.get()
        out = self.root_dir / "exports"
        out.mkdir(parents=True, exist_ok=True)
        dst = out / f"scan_{Path(self.sum.get()).stem}_{_AGG[self.agg.get()]}.csv"
        keys = sorted(ser)
        xs = sorted({x for pts in ser.values() for x, _y in pts})
        val = {k: dict(pts) for k, pts in ser.items()}
        with open(dst, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f)
            w.writerow([xcol] + keys)
            for x in xs:
                w.writerow([x] + [val[k].get(x, "") for k in keys])
        self.lbl.configure(text=f"已导出 {dst.name}")

    def _export_png(self):
        if not self._spec or not self._spec[1]:
            self.lbl.configure(text="无可导出数据")
            return
        ser, title = self._spec[1], self._spec[2]
        out = self.root_dir / "exports"
        out.mkdir(parents=True, exist_ok=True)
        dst = out / f"scan_{Path(self.sum.get()).stem}.png"
        if not matplotlib_available() and not self._ensure():
            self.lbl.configure(text="未启用 matplotlib，PNG 未导出（Canvas 显示不受影响）")
            self._sync_mpl_btn()
            return
        p = render_png(ser, dst, title=f"{title} vs {self.xcol.get()}",
                       xlabel=self.xcol.get(), ylabel="归一化值" if self.norm.get() else "值")
        self.lbl.configure(text=(f"已导出 {dst.name}" if p else "matplotlib 出图失败（已保留 Canvas 显示）"))
        self._sync_mpl_btn()


class ScanWindowMixin:
    def _open_scan_window(self):
        if not getattr(self, "_scan_wins", None):
            self._scan_wins = []
        self._scan_wins.append(ScanWindow(self.root, self.s.workspace,
                                          ensure_cb=self._ensure_plot_backend))
