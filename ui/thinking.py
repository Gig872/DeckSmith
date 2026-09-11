# -*- coding: utf-8 -*-
"""ThinkingMixin：思考/工作窗口（实时事件显示）。"""
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText


class ThinkingMixin:
    def _toggle_think_win(self):
        if self.var_think_win.get():
            self._open_thinking()
        else:
            self._close_thinking()

    def _close_thinking(self):
        self.var_think_win.set(False)
        if self._think_win and self._think_win.winfo_exists():
            self._think_win.destroy()
        self._think_win = None
        self._think_txt = None

    def _open_thinking(self):
        self.var_think_win.set(True)
        if self._think_win and self._think_win.winfo_exists():
            self._think_win.deiconify()
            self._think_win.lift()
            return
        w = tk.Toplevel(self.root)
        w.title("思考 / 工作窗口 —— 实时")
        w.geometry("760x580")
        w.protocol("WM_DELETE_WINDOW", self._close_thinking)
        self._think_win = w
        bar = ttk.Frame(w)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Label(bar, text="agent 的思考与工具调用（实时）", foreground="#666").pack(side="left")
        ttk.Button(bar, text="清空", command=self._clear_thinking).pack(side="right")
        ttk.Button(bar, text="复制全部",
                   command=lambda: (self.root.clipboard_clear(),
                                    self.root.clipboard_append(self._think_txt.get("1.0", "end")))).pack(side="right", padx=6)
        self._think_txt = ScrolledText(w, wrap="word", font=("Consolas", 10))
        self._think_txt.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self._render_thinking()

    def _clear_thinking(self):
        self._events.clear()
        if self._think_txt:
            self._think_txt.delete("1.0", "end")

    def _render_thinking(self):
        if self._think_txt and self._think_txt.winfo_exists():
            self._think_txt.delete("1.0", "end")
            self._think_txt.insert("1.0", "\n".join(self._events))
            self._think_txt.see("end")

    def _on_event(self, kind: str, data: dict):
        self.q.put(("ev", kind, data))     # 从 worker 线程抛给 UI 线程
