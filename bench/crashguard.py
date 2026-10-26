# -*- coding: utf-8 -*-
"""欠费截断保护：API 额度耗尽时立即停止，且**不把受影响的任务记为失败**。

为什么必须单独处理：
  额度不足是**实验环境**问题，不是被测系统的能力问题。若按普通异常吞掉，
  剩余题会被记成 crashed/exec_ok=False，直接污染 R_exec / R_phys / R_sem。
  所以：识别 → 外传 → 截断 → 落标记，由分析端据此剔除"被截断的尾巴"。
"""
from __future__ import annotations

import os
import time

MARK = "OUT_OF_CREDIT"


def mark_out_of_credit(here: str, model: str = "", err: str = "") -> str:
    """在评测目录落一个欠费标记文件（含时间与错误摘要）。"""
    p = os.path.join(here, MARK)
    try:
        with open(p, "w", encoding="utf-8") as f:
            f.write(f"time={time.strftime('%Y-%m-%d %H:%M:%S')}\nmodel={model}\n{err[:400]}\n")
    except OSError:
        pass
    return p


def is_out_of_credit(here: str) -> bool:
    return os.path.isfile(os.path.join(here, MARK))


def clear_mark(here: str) -> None:
    """开跑前清掉旧标记，避免上次的欠费影响这次的判定。"""
    p = os.path.join(here, MARK)
    try:
        if os.path.isfile(p):
            os.remove(p)
    except OSError:
        pass


# ---------------- 批次互斥锁 ----------------
# 为什么需要：同一 (条件, 标签) 的两个 runner 会**共用同一批工作目录**
# （workspace_k{cond}{tag}_w{i}），而 harness.clear_workspace 每题清空目录 →
# 两组会互相删掉对方刚写好的产物卡，导致评测时找不到文件（n_errors=None）。
# 实测踩过两次（_half 与 _oral）。

def _alive(pid: int) -> bool:
    try:
        import subprocess
        r = subprocess.run(["tasklist", "/FI", f"PID eq {int(pid)}"],
                           capture_output=True, text=True, timeout=20)
        return str(pid) in (r.stdout or "")
    except Exception:  # noqa: BLE001
        return False


def _lock_path(here: str, tag: str) -> str:
    return os.path.join(here, ".lock_" + (tag or "main"))


def acquire_lock(here: str, tag: str):
    """取得该批次的互斥锁。返回 (ok, path, 占用者 pid)。"""
    import json
    p = _lock_path(here, tag)
    if os.path.isfile(p):
        try:
            d = json.loads(open(p, encoding="utf-8").read())
            opid = int(d.get("pid") or 0)
        except Exception:  # noqa: BLE001
            opid = 0
        if opid and _alive(opid):
            return False, p, opid
    try:
        with open(p, "w", encoding="utf-8") as f:
            json.dump({"pid": os.getpid(), "ts": time.time()}, f)
    except OSError:
        pass
    return True, p, 0


def release_lock(path: str) -> None:
    try:
        if path and os.path.isfile(path):
            os.remove(path)
    except OSError:
        pass
