# -*- coding: utf-8 -*-
"""实时进度窗口：悬浮小窗，每 2 秒自刷进度 / 判定 / token / 分族表。

用法： python bench/progresswin.py
"""
from __future__ import annotations

import os
import sys
import tkinter as tk
from tkinter import ttk
from tkinter.scrolledtext import ScrolledText

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from progress import collect, render_text  # noqa: E402

REFRESH_MS = 2000


class ProgressWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("DeckSmith 评测台 · 实时进度")
        self.root.geometry("620x520")
        try:
            self.root.attributes("-topmost", True)
        except tk.TclError:
            pass

        top = ttk.Frame(self.root)
        top.pack(fill="x", padx=10, pady=(10, 4))
        ttk.Label(top, text="总进度").pack(side="left")
        self.pb = ttk.Progressbar(top, length=300, maximum=100, mode="determinate")
        self.pb.pack(side="left", padx=8)
        self.lbl = ttk.Label(top, text="")
        self.lbl.pack(side="left")
        ttk.Button(top, text="立即刷新", command=self.refresh).pack(side="right")

        self.txt = ScrolledText(self.root, wrap="none", font=("Consolas", 10))
        self.txt.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt.configure(state="disabled")

        self.refresh()
        self.root.after(REFRESH_MS, self._tick)

    def _tick(self):
        self.refresh()
        self.root.after(REFRESH_MS, self._tick)

    def refresh(self):
        try:
            d = collect()
        except Exception as e:  # noqa: BLE001
            d = None
            text = f"(读取失败: {e})"
        if d:
            text = render_text(d)
            self.pb["value"] = d["frac"] * 100
            self.lbl.configure(
                text=f"{d.get('bar_label','')} {d.get('bar_done',d['n'])}/"
                     f"{d.get('bar_total',d['total'])}  {d['frac']*100:.1f}%")
        self.txt.configure(state="normal")
        self.txt.delete("1.0", "end")
        self.txt.insert("1.0", text)
        self.txt.configure(state="disabled")

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    import traceback
    try:
        print("窗口启动中…", flush=True)
        ProgressWindow().run()
        print("窗口正常关闭（mainloop 返回）", flush=True)
    except Exception:  # noqa: BLE001
        traceback.print_exc()
