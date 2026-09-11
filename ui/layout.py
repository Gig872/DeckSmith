# -*- coding: utf-8 -*-
"""LayoutMixin：整体布局（整页滚动 + 左参数 + 右 对话/用量/卡片/结果）。"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


class LayoutMixin:
    # ================= 整页滚动 =================
    def _build_scroll_body(self):
        holder = ttk.Frame(self.root)
        holder.pack(fill="both", expand=True, padx=8, pady=8)
        self.canvas_holder = holder
        self.canvas = tk.Canvas(holder, highlightthickness=0)
        vsb = ttk.Scrollbar(holder, orient="vertical", command=self.canvas.yview)
        self.canvas.configure(yscrollcommand=vsb.set)
        vsb.pack(side="right", fill="y")
        self.canvas.pack(side="left", fill="both", expand=True)

        body = ttk.Frame(self.canvas)
        self.body = body
        self._win = self.canvas.create_window((0, 0), window=body, anchor="nw")
        body.bind("<Configure>", lambda _e: self.canvas.configure(scrollregion=self.canvas.bbox("all")))
        self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfigure(self._win, width=e.width))

        self._build_params_panel(body)
        self._build_main_panel(body)

    def _on_wheel(self, event):
        # 鼠标悬停在文本控件上时，交给文本自己滚动；否则整页滚动
        try:
            w = self.root.winfo_containing(event.x_root, event.y_root)
        except Exception:
            w = None
        if isinstance(w, (tk.Text, tk.Listbox)):
            return
        self.canvas.yview_scroll(-1 if event.delta > 0 else 1, "units")

    # ---- 左：已规范参数 ----
    def _build_params_panel(self, body):
        left = ttk.Frame(body)
        left.pack(side="left", fill="y")
        p = ttk.LabelFrame(left, text="已规范参数（需求/意图/批量框架）", padding=6)
        p.pack(fill="both", expand=True)
        self.txt_params = ScrolledText(p, width=23, height=32, wrap="word", state="disabled",
                                       font=("Consolas", 11))
        self.txt_params.pack(fill="both", expand=True)
        ttk.Button(p, text="刷新参数", command=lambda: self._refresh_params(True)).pack(anchor="e", pady=(4, 0))

    # ---- 右：对话/用量/卡片/结果 ----
    def _build_main_panel(self, body):
        right = ttk.Frame(body)
        right.pack(side="left", fill="both", expand=True, padx=(8, 0))

        c = ttk.LabelFrame(right, text="对话", padding=6)
        c.pack(fill="both", expand=True)
        self.chat = ScrolledText(c, wrap="word", state="disabled", height=32)
        self.chat.pack(fill="both", expand=True)
        self.chat.tag_config("你", foreground="#0a5")
        self.chat.tag_config("agent", foreground="#036")
        self.chat.tag_config("提问", foreground="#a30")
        self.chat.bind("<Double-Button-1>", lambda _e: self._glossary_sel())

        row = ttk.Frame(c)
        row.pack(fill="x", pady=(6, 0))
        self.lbl_hint = ttk.Label(row, text="输入需求：", foreground="#666")
        self.lbl_hint.pack(side="left")
        self.var_in = tk.StringVar()
        self.entry = ttk.Entry(row, textvariable=self.var_in)
        self.entry.pack(side="left", fill="x", expand=True, padx=(4, 6))
        self.entry.bind("<Return>", lambda _e: self._send())
        self.btn_send = ttk.Button(row, text="发送", command=self._send)
        self.btn_send.pack(side="left")

        u = ttk.LabelFrame(right, text="用量 / 计费", padding=6)
        u.pack(fill="x", pady=(8, 0))
        self.lbl_usage = ttk.Label(u, text="(尚无用量)", justify="left", font=("Consolas", 11))
        self.lbl_usage.pack(side="left", anchor="nw")
        ttk.Button(u, text="刷新用量", command=self._refresh_usage).pack(side="right", anchor="ne")

        self._build_card_panel(right)
        self._build_result_panel(right)

    def _build_card_panel(self, right):
        card = ttk.LabelFrame(right, text="输入卡（无注释版）", padding=6)
        card.pack(fill="x", pady=(8, 0))
        bar = ttk.Frame(card)
        bar.pack(fill="x")
        self.btn_card = ttk.Button(bar, text="▸ 展开", width=8, command=self._toggle_card)
        self.btn_card.pack(side="left")
        self.lbl_card = ttk.Label(bar, text="(暂无卡片)", foreground="#666")
        self.lbl_card.pack(side="left", padx=6)
        # 默认折叠：让对话区占主导
        self.txt_card = ScrolledText(card, height=14, wrap="none", font=("Consolas", 11))

    def _build_result_panel(self, right):
        res = ttk.LabelFrame(right, text="结果表（最近一次真跑的关键读数）", padding=6)
        res.pack(fill="both", pady=(8, 0))
        bar = ttk.Frame(res)
        bar.pack(fill="x")
        self.btn_res = ttk.Button(bar, text="▸ 展开", width=8, command=self._toggle_res)
        self.btn_res.pack(side="left")
        self.lbl_res = ttk.Label(bar, text="(尚无运行)", foreground="#666")
        self.lbl_res.pack(side="left", padx=6)
        ttk.Button(bar, text="刷新结果", command=self._refresh_res).pack(side="right")
        self.txt_res = ScrolledText(res, height=12, wrap="none", font=("Consolas", 11))
        # 默认收起：不 pack

    def _toggle_card(self):
        if self.txt_card.winfo_ismapped():
            self.txt_card.pack_forget()
            self.btn_card.configure(text="▸ 展开")
        else:
            self.txt_card.pack(fill="both", expand=True, pady=(4, 0))
            self.btn_card.configure(text="▾ 收起")

    def _toggle_res(self):
        if self.txt_res.winfo_ismapped():
            self.txt_res.pack_forget()
            self.btn_res.configure(text="▸ 展开")
        else:
            self.txt_res.pack(fill="both", expand=True, pady=(4, 0))
            self.btn_res.configure(text="▾ 收起")
            self._refresh_res()
