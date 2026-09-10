# -*- coding: utf-8 -*-
"""可插拔工具注册表。

加工具 = 在 tools/ 下写一个函数并加 @tool 装饰器（或 import 任意模块触发注册）。
框架只认 schema；工具本身完全解耦，便于增删改。
"""
from __future__ import annotations

import importlib
import pkgutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass
class Tool:
    name: str
    desc: str
    params: dict          # JSON Schema properties
    required: list[str]
    fn: Callable

    def schema(self) -> dict:
        return {"type": "function", "function": {
            "name": self.name, "description": self.desc,
            "parameters": {"type": "object", "properties": self.params,
                           "required": self.required or []},
        }}


_REG: dict[str, Tool] = {}


def tool(name: str, desc: str, params: dict | None = None, required: list[str] | None = None):
    """装饰器：把函数注册为工具。"""
    def deco(fn: Callable) -> Callable:
        _REG[name] = Tool(name, desc, params or {}, required or [], fn)
        return fn
    return deco


def schemas() -> list[dict]:
    return [t.schema() for t in _REG.values()]


def call(name: str, args: dict) -> str:
    t = _REG.get(name)
    if not t:
        return f"[错误] 未知工具 {name}"
    try:
        out = t.fn(**(args or {}))
        return out if isinstance(out, str) else str(out)
    except Exception as e:  # 工具异常回喂给模型，不崩循环
        return f"[工具 {name} 异常] {e}"


def names() -> list[str]:
    return list(_REG)


# ---- 每任务工具调用计数（用于对"只读/查询类"工具限流，防只查不动手）----
_COUNTS: dict[str, int] = {}


def bump(name: str) -> int:
    _COUNTS[name] = _COUNTS.get(name, 0) + 1
    return _COUNTS[name]


def reset_counts() -> None:
    _COUNTS.clear()


# 已知工具模块（冻结/PyInstaller 环境下 pkgutil 可能枚举不到，用此兜底）
_KNOWN_TOOLS = ["ask", "basic", "files", "knowledge", "notes", "relap5",
                "session", "shell", "web", "batch"]


def load_plugins(package: str = "tools") -> list[str]:
    """导入 tools 包里所有子模块，触发其中的 @tool 注册。
    优先枚举；枚举不到（如打包成 exe）时用已知清单兜底，确保工具不丢。"""
    pkg = importlib.import_module(package)
    names: set = set()
    try:
        for m in pkgutil.iter_modules(pkg.__path__):
            if not m.name.startswith("_"):
                names.add(m.name)
    except Exception:
        pass
    names |= set(_KNOWN_TOOLS)
    loaded = []
    for name in sorted(names):
        if name.startswith("_"):
            continue
        try:
            importlib.import_module(f"{package}.{name}")
            loaded.append(name)
        except Exception:
            pass
    return loaded
