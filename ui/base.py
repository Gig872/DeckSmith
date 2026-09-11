# -*- coding: utf-8 -*-
"""BaseMixin：状态初始化、窗口图标、事件泵调度。"""
from __future__ import annotations

import queue
import threading
import tkinter as tk
from pathlib import Path

import registry
from config import load
from core import Session
from usage import Usage
from version import __version__
import tools.ask as ask


class BaseMixin:
    # ---- 初始化 ----
    def __init__(self, root: tk.Tk):
        self.root = root
        root.title(f"卡匠 DeckSmith v{__version__} · RELAP5 建模智能体")
        root.geometry("1320x880")

        self.s = load()
        self.usage = Usage()
        self.sess: Session | None = None
        self.sess_name = ""
        self.q: queue.Queue = queue.Queue()
        self._busy = False
        self._pending = None
        self.var_trace = tk.BooleanVar(value=True)
        self.var_think_win = tk.BooleanVar(value=False)   # 视图：思考窗开关
        self.var_thinking = tk.BooleanVar(value=False)    # 模型：思考模式开关
        self._settings_open = False
        self._params_sig = None
        self._think_win = None          # 思考/工作窗口（Toplevel）
        self._think_txt = None
        self._events: list[str] = []    # 事件缓冲（窗口未开也留存）

        registry.load_plugins("tools")
        ask.set_asker(self._asker)

        self._build_topbar()
        self._build_settings_panel()
        self._build_scroll_body()
        self._load_cfg_into_ui()
        self._refresh_sessions()
        self._set_status("就绪")
        self._set_usage_text("(尚无用量)")
        self._greet()

        self._set_icon()
        self.root.bind_all("<MouseWheel>", self._on_wheel, add="+")
        self.root.after(80, self._drain)
        self.root.after(400, self._poll_params)

    # ---- 窗口图标 ----
    def _set_icon(self):
        base = Path(__file__).resolve().parent.parent / "assets"   # ui/ 的上一级 = 项目根
        png, ico = base / "icon.png", base / "icon.ico"
        try:
            if png.is_file():
                self._icon_img = tk.PhotoImage(file=str(png))     # 保住引用，防被回收
                self.root.iconphoto(True, self._icon_img)
        except Exception:  # noqa: BLE001
            pass
        try:
            if ico.is_file():
                self.root.iconbitmap(str(ico))                    # Windows 任务栏/标题栏
        except Exception:  # noqa: BLE001
            pass
