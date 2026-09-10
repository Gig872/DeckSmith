# -*- coding: utf-8 -*-
"""当前会话上下文（无依赖，供 core 与工具共享，避免循环导入）。

单线程使用：任何时刻只有一个"当前会话"。工具（remember_requirement /
list_requirements / set_user_level 等）通过 current() 读写会话状态。
"""
from __future__ import annotations

_CUR = None


def set_current(sess) -> None:
    global _CUR
    _CUR = sess


def current():
    return _CUR
