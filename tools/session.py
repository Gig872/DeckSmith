# -*- coding: utf-8 -*-
"""会话/教学工具：把"已确认需求 / 用户水平"变成可读写的一等状态。

供第 4 层（交互与教学内核）使用：缺项清单逐项确认，收齐再建卡；
水平判定驱动 导师 / 翻译器 模式切换。
"""
from __future__ import annotations

import sessionctx
from registry import tool


def _sess():
    return sessionctx.current()


@tool("set_user_level", "记录用户水平，决定 导师(novice)/翻译器(expert) 模式。",
      {"level": {"type": "string", "description": "novice 或 expert"}}, ["level"])
def set_user_level(level: str) -> str:
    s = _sess()
    if s is None:
        return "[提示] 当前非会话模式，水平已忽略。"
    lv = str(level or "").strip().lower()
    if lv not in ("novice", "expert", "unknown"):
        return "[提示] level 只能是 novice / expert。"
    s.set_level(lv)
    mode = {"novice": "导师模式", "expert": "翻译器模式", "unknown": "未定"}.get(lv)
    return f"已记录用户水平：{lv}（{mode}）"


@tool("remember_requirement", "记录一条【已确认】需求（键/值/来源），供建模前核对、跨轮记忆。",
      {"key": {"type": "string", "description": "需求项，如 部件类型/边界压力/目标部件"},
       "value": {"type": "string", "description": "确认后的取值"},
       "source": {"type": "string", "description": "来源：user=用户明确 / default=采纳默认"}},
      ["key", "value"])
def remember_requirement(key: str, value: str, source: str = "user") -> str:
    s = _sess()
    if s is None:
        return "[提示] 当前非会话模式，需求未记录。"
    s.remember(key, value, source)
    tag = "用户明确" if str(source).lower() != "default" else "默认(可改)"
    return f"已确认需求：{key} = {value} 〔{tag}〕"


@tool("list_requirements", "列出本会话已确认的全部需求（建卡前应据此核对，避免臆造）。", {})
def list_requirements() -> str:
    s = _sess()
    if s is None:
        return "(当前非会话模式，无会话需求)"
    return s.requirements_text()


@tool("set_batch_plan",
      "批量仿真前，先与用户商定并记录**批量框架**：基准模型、要扫哪些自变量、要看哪些因变量、"
      "工况类型、以及各扫描变量的取值范围（范围需向用户确认后再填）。",
      {"base_model": {"type": "string", "description": "基准模型/部件构成"},
       "vary": {"type": "string", "description": "要扫的自变量（参数名 + 取值范围/步长）"},
       "observe": {"type": "string", "description": "要观察/汇总的因变量（如出口温度、压降、流量）"},
       "cases": {"type": "string", "description": "预计工况数 / 组合方式"}},
      ["base_model", "vary", "observe"])
def set_batch_plan(base_model: str, vary: str, observe: str, cases: str = "") -> str:
    s = _sess()
    txt = f"基准模型：{base_model}\n扫描变量/范围：{vary}\n观察量：{observe}\n工况数：{cases or '(待定)'}"
    if s is None:
        return "[提示] 当前非会话模式，批量框架已忽略。\n" + txt
    s.meta["batch"] = {"base_model": base_model, "vary": vary, "observe": observe, "cases": cases}
    return "已记录批量仿真框架：\n" + txt


@tool("set_model_intent",
      "建模前写下**物理意图**：这是什么系统、靠什么驱动、能量从哪来/到哪去、预判的合理范围。"
      "写不出自洽的意图，说明设计还没想清楚——先别建卡。",
      {"scenario": {"type": "string", "description": "物理场景：这是什么系统/工质"},
       "driver": {"type": "string", "description": "驱动力：压差/泵/重力/定流量…"},
       "energy": {"type": "string", "description": "能量来源与去向：有无加热/做功/排热，是否平衡"},
       "expected": {"type": "string", "description": "预判范围：压力/温度/流量的合理量级"}},
      ["scenario", "driver", "energy", "expected"])
def set_model_intent(scenario: str, driver: str, energy: str,
                     expected: str) -> str:
    s = _sess()
    txt = (f"场景：{scenario}\n驱动：{driver}\n能量：{energy}\n预判：{expected}")
    if s is None:
        return "[提示] 当前非会话模式，意图已忽略。\n" + txt
    s.meta["intent"] = {"scenario": scenario, "driver": driver,
                        "energy": energy, "expected": expected}
    return "已记录建模意图：\n" + txt
