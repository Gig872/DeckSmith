# -*- coding: utf-8 -*-
"""卡匠 DeckSmith · RELAP5 建模智能体 —— 桌面入口。

界面实现已拆分到 `ui/` 包（各职责 Mixin，见 ui/app.py）。
启动：python decksmith.py ；打包 exe：build_exe.bat
"""
from __future__ import annotations

from ui.app import main

if __name__ == "__main__":
    raise SystemExit(main())
