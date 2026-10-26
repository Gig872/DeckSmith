# -*- coding: utf-8 -*-
"""评测条件装配：带库 / 无库。

必须在 import config / tools **之前**调用 setup(mode)，否则知识库路径会被固定成默认值。

  mode = "off"（无库）：样例库物理移出（bench/holdout），agent 三档皆空。默认即此。
  mode = "on" （带库）：把 holdout 里的卡装配成评测库（bench/eval_lib），
                        reference 指向只读库，learned 由每题从 learned_seed 重播。

**写入隔离**：智能体的 `save_example(lib="agent")` 会写参考库的 agent 档。
评测期间必须把这个写口重定向到题目私有目录（AGENT_SAVE_AGENT_DIR），
否则运行中自存的卡会被同一批次后续题目检索到——2026-09-14 的无库批次
就因此有 19/55 题检索到了同批自存卡，污染了「无库」条件。
"""
from __future__ import annotations

import glob
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
LIB = os.path.join(HERE, "eval_lib")


def _purge_stale(empty: str) -> list[str]:
    """无库条件必须**真空**：清掉历史批次残留在空库目录里的卡。

    只在评测装配时执行；命中即说明上一次隔离失败，须在日志中显式告警。
    """
    stale = []
    for p in glob.glob(os.path.join(empty, "**", "*.i"), recursive=True):
        try:
            os.remove(p)
            stale.append(p)
        except OSError:
            pass
    return stale


def setup(mode: str = "off") -> str:
    mode = (mode or "off").lower()
    ws = os.environ.get("AGENT_WORKSPACE")
    # 写口重定向：题目私有目录；由 harness.clear_workspace 每题清空
    if ws:
        os.environ.setdefault("AGENT_SAVE_AGENT_DIR", os.path.join(ws, "agent_saved"))
    if mode == "off-strict":
        # **严格空库**：每个 worker 自己的空库，且存与取指向同一目录
        # （自存卡只对本题可见，题间清空）。两道泄漏都被关闭：
        #   跨题自存卡（原本写的是共享 agent 档）、
        #   命令行越界读卡（2026-10-17 起 tools/shell.py 已有越界检查）。
        base = os.path.join(ws or LIB, "eval_empty")
        for sub in ("learned", os.path.join("reference", "human"),
                    os.path.join("reference", "agent")):
            os.makedirs(os.path.join(base, sub), exist_ok=True)
        os.environ["AGENT_REFERENCE_DIR"] = os.path.join(base, "reference")
        os.environ["AGENT_LEARNED_SEED"] = os.path.join(base, "learned")
        os.environ["AGENT_SAVE_AGENT_DIR"] = os.path.join(base, "reference", "agent")
        os.environ["AGENT_STRICT_EMPTY"] = "1"
        return mode
    if mode == "on":
        os.environ["AGENT_REFERENCE_DIR"] = os.path.join(LIB, "reference")
        os.environ["AGENT_LEARNED_SEED"] = os.path.join(LIB, "learned_seed")
    else:
        # 无库：显式指向空目录，杜绝回落到真实知识库
        empty = os.path.join(LIB, "empty")
        os.makedirs(os.path.join(empty, "reference"), exist_ok=True)
        os.makedirs(os.path.join(empty, "learned"), exist_ok=True)
        stale = _purge_stale(empty)
        if stale:
            print(f"[evalenv] 警告：无库目录发现 {len(stale)} 张残留卡，已清除：",
                  file=sys.stderr, flush=True)
            for p in stale[:10]:
                print("  ", p, file=sys.stderr, flush=True)
        os.environ["AGENT_REFERENCE_DIR"] = os.path.join(empty, "reference")
        os.environ["AGENT_LEARNED_SEED"] = os.path.join(empty, "learned")
    return mode


def mode_from_argv(argv) -> str:
    """在 import config 之前，从命令行抢先解析 --knowledge。"""
    try:
        i = list(argv).index("--knowledge")
        return list(argv)[i + 1]
    except (ValueError, IndexError):
        return os.environ.get("AGENT_KNOWLEDGE", "off")
