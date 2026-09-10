# -*- coding: utf-8 -*-
"""沙箱执行工具：run_command / python_exec。

沙箱规则（防死循环空转 + 防误伤）：
  - cwd 固定在工作目录；超时上限；输出截断；
  - 危险命令黑名单直接拒绝。
"""
from __future__ import annotations

import re
import subprocess
import sys

from registry import tool
from config import load

_BASE = load().workspace
_TIMEOUT_CAP = 120
_BAD = re.compile(
    r"(rm\s+-rf\s+/|del\s+/[fsq]|format\s+[a-z]:|shutdown|mkfs|:\(\)\s*\{|diskpart|>\s*/dev/sd)",
    re.I,
)


def _run(cmd, timeout: int, shell: bool) -> str:
    if isinstance(cmd, str) and _BAD.search(cmd):
        return "[沙箱拒绝] 命令命中危险黑名单。"
    t = min(int(timeout or 60), _TIMEOUT_CAP)
    try:
        p = subprocess.run(cmd, cwd=_BASE, shell=shell, capture_output=True,
                           timeout=t, text=True, errors="replace")
    except subprocess.TimeoutExpired:
        return f"[超时] 命令超过 {t}s 未结束，已终止。"
    except Exception as e:  # noqa: BLE001
        return f"[执行失败] {e}"
    out = (p.stdout or "") + (("\n[stderr]\n" + p.stderr) if p.stderr else "")
    out = out.strip() or "(无输出)"
    return f"[rc={p.returncode}]\n" + out[:2000]


@tool("run_command", "在工作目录中执行一条 shell 命令（沙箱内，超时/截断）。",
      {"cmd": {"type": "string"}, "timeout": {"type": "integer"}}, ["cmd"])
def run_command(cmd: str, timeout: int = 60) -> str:
    return _run(cmd, timeout, shell=True)


@tool("python_exec", "在工作目录中执行一段 Python 代码（沙箱内）。",
      {"code": {"type": "string"}, "timeout": {"type": "integer"}}, ["code"])
def python_exec(code: str, timeout: int = 60) -> str:
    return _run([sys.executable, "-c", code], timeout, shell=False)
