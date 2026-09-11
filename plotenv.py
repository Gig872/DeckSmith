# -*- coding: utf-8 -*-
"""绘图后端（matplotlib）的环境探测与**自动安装**（可选，不影响零依赖 Canvas 出图）。

核心永远零依赖；只有用户想要更精细的静态图（PNG）时才：
  **探库 → 缺则征询后自动 pip 安装（带提示）→ 成功用 matplotlib，失败优雅降级回 Canvas**。
打包版（exe）内置解释器无法 pip，改用 `build_exe.bat mpl` 的带库构建。
"""
from __future__ import annotations

import subprocess
import sys
from typing import Callable, Optional

from postprocess.plot import matplotlib_available

_PKG = "matplotlib"
Progress = Optional[Callable[[str], None]]


def available() -> bool:
    """matplotlib 是否可用（能 import）。"""
    return matplotlib_available()


def is_frozen() -> bool:
    return bool(getattr(sys, "frozen", False))


def can_install() -> tuple[bool, str]:
    """当前环境能否自动安装。返回 (可安装?, 说明)。"""
    if is_frozen():
        return False, ("当前是打包版（exe）内置解释器，无法 pip 安装。"
                       "请改用带 matplotlib 的构建（build_exe.bat mpl），"
                       "或继续用零依赖 Canvas 出图（功能不受影响）。")
    return True, ""


def _pip_cmd() -> list[str]:
    return [sys.executable, "-m", "pip", "install", "--upgrade", _PKG]


def install(progress: Progress = None, timeout: int = 900) -> tuple[bool, str]:
    """自动 pip 安装 matplotlib；progress(line) 实时回显。返回 (成功?, 说明)。"""
    ok, why = can_install()
    if not ok:
        return False, why
    if available():
        return True, "matplotlib 已可用（无需安装）。"
    cmd = _pip_cmd()
    if progress:
        progress("$ " + " ".join(cmd))
    try:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, encoding="utf-8", errors="replace")
    except Exception as e:  # noqa: BLE001
        return False, f"无法启动 pip：{e}"
    tail: list[str] = []
    try:
        for line in proc.stdout:          # type: ignore[union-attr]
            line = line.rstrip()
            tail.append(line)
            if len(tail) > 200:
                tail.pop(0)
            if progress:
                progress(line)
        proc.wait(timeout=timeout)
    except Exception as e:  # noqa: BLE001
        try:
            proc.kill()
        except Exception:  # noqa: BLE001
            pass
        return False, f"安装过程出错：{e}"
    if proc.returncode != 0:
        return False, "pip 返回非零：" + (tail[-1] if tail else "（无输出）")
    if available():
        return True, "安装成功，matplotlib 已可用。"
    return True, "pip 已完成；若仍提示不可用，重启本程序即可生效。"


def ensure(confirm: Callable[[str], bool], progress: Progress = None) -> tuple[bool, str]:
    """探库 → 缺则征询 confirm(提示语) → 自动安装。返回 (最终可用?, 说明)。"""
    if available():
        return True, "matplotlib 已可用。"
    ok, why = can_install()
    if not ok:
        return False, why
    if not confirm("未检测到 matplotlib（绘图增强库，约 30–50MB，需联网 pip）。\n"
                   "是否现在自动安装，以获得更精细的 PNG 出图？\n\n"
                   "（选『否』将用零依赖 Canvas 出图，功能不受影响。）"):
        return False, "已取消安装；改用零依赖 Canvas 出图。"
    ok, msg = install(progress)
    return (ok and available()), msg
