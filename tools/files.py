# -*- coding: utf-8 -*-
"""工作目录文件工具（沙箱内）：读/写/列/改。"""
from __future__ import annotations

from registry import tool
from safety import Sandbox
from config import load

_SB = Sandbox(load().workspace)


@tool("list_files", "列出工作目录下的文件（及子目录）。", {})
def list_files() -> str:
    items = [str(p.relative_to(_SB.root)) for p in sorted(_SB.root.rglob("*")) if p.is_file()]
    return "\n".join(items) if items else "(工作目录为空)"


@tool("read_file", "读取工作目录下的文本文件（可分页）。",
      {"path": {"type": "string"},
       "max_chars": {"type": "integer", "description": "最多读多少字符，默认4000"}},
      ["path"])
def read_file(path: str, max_chars: int = 4000) -> str:
    p = _SB.resolve(path)
    if not p.is_file():
        return f"文件不存在: {path}"
    return p.read_text(encoding="utf-8", errors="replace")[: int(max_chars)]


@tool("write_file", "把文本写入工作目录下的文件（覆盖）。",
      {"path": {"type": "string"}, "text": {"type": "string"}}, ["path", "text"])
def write_file(path: str, text: str) -> str:
    p = _SB.resolve(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(text, encoding="utf-8")
    return f"已写入 {p.relative_to(_SB.root)} ({len(text)} 字符)"


@tool("edit_file", "在文件里把 old 替换成 new（首次出现）。",
      {"path": {"type": "string"}, "old": {"type": "string"}, "new": {"type": "string"}},
      ["path", "old", "new"])
def edit_file(path: str, old: str, new: str) -> str:
    p = _SB.resolve(path)
    if not p.is_file():
        return f"文件不存在: {path}"
    t = p.read_text(encoding="utf-8")
    if old not in t:
        return f"未找到要替换的内容（{old[:40]}）"
    p.write_text(t.replace(old, new, 1), encoding="utf-8")
    return "已替换"
