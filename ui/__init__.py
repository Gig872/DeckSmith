# -*- coding: utf-8 -*-
"""卡匠 DeckSmith 的桌面界面层（tkinter）。

入口：`decksmith.py` → `ui.app.main()`。
按职责拆分为若干 Mixin（base/topbar/settings/layout/sessions/chat/panels/thinking/misc），
最终在 `ui.app.App` 组合。此 __init__ 保持空，避免 import 本包即拉入 tkinter。
"""
