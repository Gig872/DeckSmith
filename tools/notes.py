# -*- coding: utf-8 -*-
"""记忆工具：remember（写笔记/教训）+ recall（检索）。sandbox 内 notes/。"""
from __future__ import annotations

import json
import time
from pathlib import Path

from registry import tool
from config import load

_NOTES = Path(load().workspace) / "notes"


@tool("remember", "记下一条笔记/结论/教训，供以后 recall。",
      {"text": {"type": "string"}, "tag": {"type": "string"}}, ["text"])
def remember(text: str, tag: str = "general") -> str:
    _NOTES.mkdir(parents=True, exist_ok=True)
    p = _NOTES / f"{tag}.jsonl"
    with p.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"t": time.strftime("%Y-%m-%d %H:%M"), "text": text},
                           ensure_ascii=False) + "\n")
    return f"已记入 notes/{tag}.jsonl"


@tool("recall", "检索已记的笔记（按关键词子串匹配）。",
      {"query": {"type": "string"}, "limit": {"type": "integer"}}, ["query"])
def recall(query: str, limit: int = 5) -> str:
    if not _NOTES.is_dir():
        return "(暂无笔记)"
    q = query.lower()
    hits = []
    for p in sorted(_NOTES.glob("*.jsonl")):
        for line in p.read_text(encoding="utf-8", errors="replace").splitlines():
            if q in line.lower():
                hits.append(f"[{p.stem}] {line}")
    return "\n".join(hits[: int(limit)]) if hits else "(未命中笔记)"
