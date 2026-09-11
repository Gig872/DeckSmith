# -*- coding: utf-8 -*-
"""把各 Mixin 组合成最终 App，并提供 main()。"""
from __future__ import annotations

import tkinter as tk

from .base import BaseMixin
from .topbar import TopbarMixin
from .settings import SettingsMixin
from .layout import LayoutMixin
from .sessions import SessionsMixin
from .chat import ChatMixin
from .panels import PanelsMixin
from .thinking import ThinkingMixin
from .misc import MiscMixin


class App(TopbarMixin, SettingsMixin, LayoutMixin, SessionsMixin,
          ChatMixin, PanelsMixin, ThinkingMixin, MiscMixin, BaseMixin):
    """桌面应用：按职责分散到各 Mixin，组合于此。"""


def main() -> int:
    # Windows：给本进程设 AppUserModelID，使**任务栏**用本程序图标（而非 python 的）
    try:
        import ctypes
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID("DeckSmith.RELAP5.Agent")
    except Exception:  # noqa: BLE001
        pass
    root = tk.Tk()
    App(root)
    root.mainloop()
    return 0
