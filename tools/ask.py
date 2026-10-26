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
    """**未注入前端的场合一律不阻塞**。

    批量评测/无人值守时 `input()` 会挂在没有 stdin 的子进程上（实测把整题卡死）。
    命令行交互由 `ui/base.py` 注入 asker，仍可正常问答；这里只兜底给一句
    明确的"无人应答"，并提示按合理假设继续、在交付说明里注明。
    """
    return "（评测/无人值守环境：无人应答。请按报告已给的物理条件作合理假设继续，并逐条注明假设。）"


@tool("ask_user",
      "向用户提问以澄清需求或补全缺失信息，返回用户的回答。"
      "注意：用户可能不直接回答而是**反问**（如'什么是边界条件'）——此时**先当导师解释清楚**"
      "（用 glossary + 通俗三段式），**再**回到原问题；**严禁**把反问当成没回答而原样重复提问。",
      {"question": {"type": "string", "description": "要问用户的问题（一次只问 1–2 项）"}}, ["question"])
def ask_user(question: str) -> str:
    fn = _ASKER or _default_asker
    ans = fn(question)
    return ans or "（用户未回答）"
