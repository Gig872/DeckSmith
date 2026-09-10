# -*- coding: utf-8 -*-
"""交互工具 ask_user：agent 主动向人提问（导师式澄清）。

CLI 下默认用 input()；将来接前端时用 set_asker(fn) 注入回调（fn(question)->answer）。
"""
from __future__ import annotations

from registry import tool

_ASKER = None


def set_asker(fn) -> None:
    """注入提问回调（前端用）。fn(question:str)->str。"""
    global _ASKER
    _ASKER = fn


def _default_asker(question: str) -> str:
    try:
        return input(f"\n[agent 提问] {question}\n> ").strip()
    except (EOFError, KeyboardInterrupt):
        return ""


@tool("ask_user",
      "向用户提问以澄清需求或补全缺失信息，返回用户的回答。"
      "注意：用户可能不直接回答而是**反问**（如'什么是边界条件'）——此时**先当导师解释清楚**"
      "（用 glossary + 通俗三段式），**再**回到原问题；**严禁**把反问当成没回答而原样重复提问。",
      {"question": {"type": "string", "description": "要问用户的问题（一次只问 1–2 项）"}}, ["question"])
def ask_user(question: str) -> str:
    fn = _ASKER or _default_asker
    ans = fn(question)
    return ans or "（用户未回答）"
