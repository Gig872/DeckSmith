# -*- coding: utf-8 -*-
"""TopbarMixin：顶栏（设置 | 视图▾ | 导出▾ | 会话 | 操作 | 状态）。"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


class TopbarMixin:
    def _build_topbar(self):
        bar = ttk.Frame(self.root)
        bar.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Button(bar, text="⚙ 设置", command=self._toggle_settings).pack(side="left")

        # 视图菜单：收纳所有"显示/窗口"类开关
        mb = ttk.Menubutton(bar, text="视图 ▾")
        mv = tk.Menu(mb, tearoff=0)
        mv.add_checkbutton(label="思考 / 工作窗口（实时）", variable=self.var_think_win,
                           command=self._toggle_think_win)
        mv.add_checkbutton(label="显示工具轨迹", variable=self.var_trace)
        mv.add_checkbutton(label="agent 出图时自动开窗", variable=self.var_auto_plot)
        mv.add_separator()
        mv.add_command(label="结果图窗口…（实时出图）", command=self._open_plot_window)
        mv.add_command(label="批量扫描趋势图…（参数→结果）", command=self._open_scan_window)
        mb["menu"] = mv
        mb.pack(side="left", padx=6)

        # 导出菜单
        mx = ttk.Menubutton(bar, text="导出 ▾")
        me = tk.Menu(mx, tearoff=0)
        me.add_command(label="会话记录…", command=self._export_chat)
        me.add_command(label="当前卡片…", command=self._export_card)
        mx["menu"] = me
        mx.pack(side="left", padx=6)

        # 会话
        ttk.Label(bar, text="会话").pack(side="left", padx=(12, 2))
        self.var_sess = tk.StringVar()
        self.cb_sess = ttk.Combobox(bar, textvariable=self.var_sess, width=16, state="readonly")
        self.cb_sess.pack(side="left")
        self.cb_sess.bind("<<ComboboxSelected>>", lambda _e: self._load_session(self.var_sess.get()))
        ttk.Button(bar, text="新建", command=self._new_session).pack(side="left", padx=4)
        self.btn_stop = ttk.Button(bar, text="停止", command=self._stop, state="disabled")
        self.btn_stop.pack(side="left", padx=4)
        ttk.Button(bar, text="术语速查", command=self._glossary_sel).pack(side="left", padx=4)
        ttk.Button(bar, text="环境检测", command=self._env_check).pack(side="left", padx=4)

        self.lbl_status = ttk.Label(bar, text="就绪", foreground="#666")
        self.lbl_status.pack(side="right")
