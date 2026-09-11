# -*- coding: utf-8 -*-
"""把 agent 的步骤事件格式化成人类可读的一行（供"思考/工作窗口"显示）。

纯函数、无 tkinter 依赖，便于单测。
"""
from __future__ import annotations

import json


def fmt_event(kind: str, d: dict) -> str:
    if kind == "step":
        return f"\n──── 第 {d.get('step', '?')} 步 ────"
    if kind == "assistant":
        out = []
        if d.get("reasoning"):
            out.append("【思考】" + d["reasoning"].strip())
        if d.get("content"):
            out.append("【模型】" + d["content"].strip())
        return "\n".join(out)
    if kind == "tool":
        try:
            a = json.dumps(d.get("args", {}), ensure_ascii=False)[:300]
        except Exception:  # noqa: BLE001
            a = str(d.get("args"))[:300]
        return f"▶ 调用 {d.get('name', '')}({a})"
    if kind == "tool_result":
        return f"◀ {d.get('name', '')} → {str(d.get('result', ''))[:800]}"
    if kind == "final":
        # 正文已在 assistant 事件里显示过，这里只给结束标记，避免重复
        return "—— 本轮结束 ——" if not d.get("stopped") else ("—— 本轮终止：" + d.get("stopped", "") + " ——")
    return ""
