# -*- coding: utf-8 -*-
"""agent-kit 入口：python run.py "需求"   （加 --dry 离线验证循环）。"""
from __future__ import annotations

import argparse
import sys

import registry
from config import load
from core import Agent, Session


def _show(out) -> None:
    print("\n===== 给用户（自然语言） =====")
    print(out.say or "(无)")
    if out.stopped:
        print(f"\n[熔断/终止] {out.stopped}")
    print("\n===== 工具轨迹（任务结果） =====")
    for t in out.trace:
        print(f"- {t['tool']}({t['args']}) -> {str(t['result'])[:120]}")
    if out.notes:
        print("\n===== 预算（目标自适应） =====")
        for n in out.notes:
            print(f"- {n}")


def main() -> int:
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
    ap = argparse.ArgumentParser(prog="agent-kit")
    ap.add_argument("text", nargs="*", help="给 agent 的自然语言需求")
    ap.add_argument("--dry", action="store_true", help="离线 dry-run（不真调模型）")
    ap.add_argument("--chat", action="store_true", help="多轮会话模式（跨轮记忆需求/模型）")
    ap.add_argument("--skills", action="store_true", help="启动时打印已加载工具与 skill")
    a = ap.parse_args()

    s = load()
    if a.dry:
        s.dry_run = True

    loaded = registry.load_plugins("tools")
    if a.skills or a.dry:
        print(f"[工具] {registry.names()}")
        print(f"[插件模块] {loaded}")

    text = " ".join(a.text).strip()

    # 多轮会话模式：跨轮保存 历史/已确认需求/用户水平
    if a.chat:
        sess = Session(s)
        print("[会话模式] 输入需求开始；空行或 Ctrl-C 退出。")
        while True:
            try:
                line = text or input("\n需求> ").strip()
            except (EOFError, KeyboardInterrupt):
                break
            text = ""
            if not line:
                break
            _show(sess.send(line))
            print(f"\n[会话状态] 轮次={sess.meta['turn']} 水平={sess.meta['user_level']}")
        return 0

    if not text:
        try:
            text = input("需求> ").strip()
        except (EOFError, KeyboardInterrupt):
            return 0
    if not text:
        return 0

    _show(Agent(s).run(text))
    return 0


if __name__ == "__main__":
    sys.exit(main())
