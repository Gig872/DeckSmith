# -*- coding: utf-8 -*-
"""基础工具：算术、时间。"""
from __future__ import annotations

import time

from registry import tool


@tool("calc", "计算一个算术表达式，如 2+3*4。",
      {"expr": {"type": "string"}}, ["expr"])
def calc(expr: str) -> str:
    return str(eval(expr, {"__builtins__": {}}, {}))


@tool("get_time", "获取当前日期时间。", {})
def get_time() -> str:
    return time.strftime("%Y-%m-%d %H:%M:%S")
