# -*- coding: utf-8 -*-
"""沙箱执行工具：run_command / python_exec。

沙箱规则（防死循环空转 + 防误伤 + **防越界**）：
  - cwd 固定在工作目录；超时上限；输出截断；
  - 危险命令黑名单直接拒绝；
  - **越界防护**：拒绝 `..` 路径穿越、以及指向工作区之外的绝对路径。
    （实测：模型用 `cd ..\\workspace_card_l30` 读到了另一个工作区的复原卡，
      `--knowledge off` 的隔离因此并不严密。python_exec 只检查 **代码文本**，
      不检查解释器自身路径。）
"""
from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

from registry import tool
from config import load

_BASE = load().workspace
_BASE_ABS = str(Path(_BASE).resolve()).lower()
_TIMEOUT_CAP = 120
_BAD = re.compile(
    r"(rm\s+-rf\s+/|del\s+/[fsq]|format\s+[a-z]:|shutdown|mkfs|:\(\)\s*\{|diskpart|>\s*/dev/sd)",
    re.I,
)
_WIN_ABS = re.compile(r"[A-Za-z]:[\\/][^\s'\"|&;<>(),]*")
# 只把「作为路径段出现的 `..`」判为穿越（贴着分隔符，或紧跟 cd/dir/type 等命令词），
# 避免把普通文本里的 `..`（如 `1.0 .. 2.0`）误伤。
_TRAV = re.compile(
    r"[\\/]\.\.(?:[\\/]|$)|\b(?:cd|pushd|dir|type|copy|move|del|tree)\s+\.\.(?:[\\/]|\s|$)",
    re.I,
)


def _escape_reason(text: str):
    """检测明显越界：`..` 路径穿越，或指向工作区之外的绝对路径。"""
    s = text or ""
    if _TRAV.search(s):
        return "包含 `..` 路径穿越"
    for m in _WIN_ABS.finditer(s):
        p = m.group(0)
        try:
            rp = str(Path(p).resolve()).lower()
        except Exception:  # noqa: BLE001
            continue
        if not rp.startswith(_BASE_ABS):
            return "引用了工作区之外的绝对路径: " + p
    return None


def _run(cmd, timeout: int, shell: bool, check_text=None) -> str:
    text = check_text if check_text is not None else (
        cmd if isinstance(cmd, str) else " ".join(str(x) for x in cmd))
    if _BAD.search(text):
        return "[沙箱拒绝] 命令命中危险黑名单。"
    esc = _escape_reason(text)
    if esc:
        return "[沙箱拒绝] " + esc + "（只允许在工作目录内操作）"
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
    return _run([sys.executable, "-c", code], timeout, shell=False, check_text=code)
