# -*- coding: utf-8 -*-
"""MiscMixin：环境检测 / 术语速查 / 导出 / 用量。"""
from __future__ import annotations

import json
import tkinter as tk
from pathlib import Path
from tkinter import filedialog, ttk
from tkinter.scrolledtext import ScrolledText

import envcheck
import registry
from config import CONFIG_FILE


class MiscMixin:
    # ================= 环境检测 =================
    def _env_check(self):
        win = tk.Toplevel(self.root)
        win.title("环境检测")
        win.geometry("640x460")

        def render():
            txt.configure(state="normal")
            txt.delete("1.0", "end")
            try:
                rows = envcheck.check()
                txt.insert("1.0", envcheck.summary(rows))
            except Exception as e:  # noqa: BLE001
                txt.insert("1.0", f"检测出错：{type(e).__name__}: {e}")
            txt.configure(state="disabled")

        bar = ttk.Frame(win)
        bar.pack(fill="x", padx=8, pady=6)
        ttk.Button(bar, text="重新检测", command=render).pack(side="left")
        ttk.Label(bar, text="✓ 通过  ✗ 需处理", foreground="#666").pack(side="left", padx=10)
        txt = ScrolledText(win, wrap="word", font=("Consolas", 11))
        txt.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        render()

    # ================= 术语速查 =================
    def _glossary_sel(self):
        try:
            sel = self.chat.get("sel.first", "sel.last").strip()
        except tk.TclError:
            sel = ""
        if not sel:
            self._log("agent", "（术语速查：请先在对话区选中一个词，再点『术语速查』或双击。）")
            return
        term = sel.splitlines()[0][:40]
        res = registry.call("glossary", {"term": term})
        self._log("agent", f"[术语] {term}\n{res}")

    # ================= 导出 =================
    def _export_chat(self):
        path = filedialog.asksaveasfilename(defaultextension=".txt",
                                            filetypes=[("文本", "*.txt"), ("Markdown", "*.md")],
                                            initialfile=(self.sess_name or "relap5_session") + ".txt")
        if not path:
            return
        Path(path).write_text(self.chat.get("1.0", "end"), encoding="utf-8")
        self._log("agent", f"已导出会话 → {path}")

    def _export_card(self):
        p = self._artifact_path()
        if not p or not p.is_file():
            return
        path = filedialog.asksaveasfilename(defaultextension=".i",
                                            filetypes=[("RELAP5 输入卡", "*.i")], initialfile=p.name)
        if not path:
            return
        Path(path).write_text(p.read_text(encoding="utf-8"), encoding="utf-8")
        self._log("agent", f"已导出卡片 → {path}")

    # ================= 用量 =================
    def _set_usage_text(self, t: str):
        self.lbl_usage.configure(text=t)

    def _refresh_usage(self):
        self._set_usage_text(self.usage.summary(self.var_model.get() or self.s.model, self._prices()))

    def _prices(self) -> dict:
        try:
            return json.loads(CONFIG_FILE.read_text(encoding="utf-8")).get("prices", {}) or {}
        except Exception:
            return {}
