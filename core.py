# -*- coding: utf-8 -*-
"""
agent 核心循环：人 → 框架(NL + tool schemas + skill) → LLM 思考并调 tool
→ tool 结果回喂 → LLM 再思考 … → 输出（① 给人的自然语言 ② 任务结果）。

高自由度：不规定流程，全由 LLM 决策；框架只提供 工具、规范、熔断、沙箱。
"""
from __future__ import annotations

import json
import re
import threading
from dataclasses import dataclass, field
from pathlib import Path

import registry
import sessionctx
from config import Settings, load, ensure_dirs
from llm import LLM, LLMError
from safety import Breaker, Guard, Sandbox, classify_goal

_RANK = {"S": 0, "M": 1, "L": 2, "XL": 3}


def _keep_recent(msgs: list, n_blocks: int = 6) -> list:
    """保留 system+user + 最近 n 个完整(assistant+tool)块，避免孤立 tool。"""
    head = msgs[:2]
    cnt, start = 0, None
    i = len(msgs) - 1
    while i >= 2:
        m = msgs[i]
        if m.get("role") == "assistant" and m.get("tool_calls"):
            cnt += 1
            if cnt == n_blocks:
                start = i
                break
        i -= 1
    return head + (msgs[start:] if start is not None else msgs[2:])


@dataclass
class Output:
    say: str = ""                       # ① 回前端给人的自然语言
    trace: list = field(default_factory=list)  # ② 任务结果/工具轨迹
    stopped: str = ""                   # 若熔断，说明原因
    notes: list = field(default_factory=list)  # 预算档位/放宽等说明
    usage: dict = field(default_factory=dict)  # 本任务累计 token 用量


class Agent:
    def __init__(self, settings: Settings | None = None, system_extra: str = ""):
        self.s = settings or load()
        ensure_dirs(self.s)
        self.llm = LLM(self.s)
        self.registry_mod = registry
        self.sandbox = Sandbox(self.s.workspace)
        self.system_extra = system_extra
        self.cancel_event = threading.Event()   # 协作式中断（界面"停止"用）

    def cancel(self) -> None:
        self.cancel_event.set()

    # ---- 组装 system：框架约定 + skill 文本 ----
    def _system(self) -> str:
        base = (
            "你首先是一个**合格的大语言模型助手**：能自然对话，听懂用户的问题并**直接、清楚地回答**"
            "（术语、原理、常识、闲聊都算），不要因为身处某个工作流程就无视用户的提问。"
            "在此基础上，你是一个**可调用工具的 RELAP5 建模 agent**：当用户确实要建模/改模型/跑算例时，"
            "用工具逐步完成，完成后用简洁的自然语言汇报结论（这部分会直接展示给用户）。"
            "需要产物时写入工作目录。**不要臆造工具结果**。"
        )
        skills = []
        sdir = Path(self.s.skills_dir)
        if sdir.is_dir():
            for p in sorted(sdir.glob("*.md")):
                skills.append(f"# skill: {p.stem}\n{p.read_text(encoding='utf-8')}")
        parts = [base] + ([self.system_extra] if self.system_extra else []) + skills
        return "\n\n".join(parts)

    # ---- 主循环 ----
    def run(self, user_text: str) -> Output:
        """一次性任务（内部走一个临时会话，便于工具读写会话状态）。"""
        sess = Session(self.s, system_extra=self.system_extra, goal=user_text, agent=self)
        return sess.send(user_text)

    # ---- 可复用的循环体：在给定 messages 上推进，供 run / Session 复用 ----
    def _loop(self, messages: list, out: Output, goal: str = "") -> Output:
        registry.reset_counts()   # 每任务重置工具调用计数（限流用）
        self.cancel_event.clear()
        guard = Guard(self.s, goal=goal)   # 按目标复杂度起档的预算
        out.notes.append(f"[预算起档 {guard.budget.tier}] {guard.budget.cur}")
        tools = registry.schemas()
        step = 0
        tot = {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
        while True:
            step += 1
            if self.cancel_event.is_set():     # 协作式中断：界面"停止"
                out.stopped = "用户中断"
                break
            # 上下文：给足；只用"当前预算的 ctx 上限"在将超窗口前成对裁剪
            ctx_len = len(json.dumps(messages, ensure_ascii=False))
            guard.ctx_peak = max(guard.ctx_peak, ctx_len)
            if ctx_len > guard.budget.cur["ctx"]:
                messages[:] = _keep_recent(messages)   # 原地裁剪，保持会话历史对象一致
            # 苛刻升级：仅在确有进展且无空转时放宽上限；随后再判熔断
            note = guard.maybe_grow(step)
            if note:
                out.notes.append(note)
            try:
                guard.tick(step)
            except Breaker as e:
                out.stopped = str(e)
                break
            try:
                msg = self.llm.complete(messages, tools=tools or None)
            except LLMError as e:
                out.stopped = f"LLM 调用失败: {e}"
                break
            u = getattr(self.llm, "last_usage", {}) or {}
            guard.tokens += int(u.get("total_tokens") or 0)
            for k in tot:
                tot[k] += int(u.get(k) or 0)
            out.usage = dict(tot)

            # 回传 assistant（含 tool_calls / reasoning）
            asst = {"role": "assistant", "content": msg.get("content") or ""}
            if msg.get("reasoning_content"):
                asst["reasoning_content"] = msg["reasoning_content"]
            if msg.get("tool_calls"):
                asst["tool_calls"] = msg["tool_calls"]
            messages.append(asst)

            calls = msg.get("tool_calls")
            if not calls:
                out.say = msg.get("content") or ""
                break

            try:
                guard.note_calls(calls)
            except Breaker as e:
                out.stopped = str(e)
                break

            for tc in calls:
                fn = tc.get("function", {})
                name = fn.get("name", "")
                try:
                    guard.note_tool(name)
                except Breaker as e:
                    out.stopped = str(e)
                    break
                try:
                    args = json.loads(fn.get("arguments") or "{}")
                except json.JSONDecodeError:
                    args = {}
                result = registry.call(name, args)
                out.trace.append({"tool": name, "args": args, "result": str(result)[:500]})
                guard.observe(step, name, str(result))   # 观测进展，供苛刻升级判断
                messages.append({"role": "tool", "tool_call_id": tc.get("id", ""),
                                 "content": str(result)})
            if out.stopped:
                break
        _heal(messages)   # 保证会话历史始终是合法的 tool_calls/tool 配对
        return out


def _heal(messages: list) -> None:
    """若末尾的 assistant tool_calls 有未回填的 tool 结果，补占位，避免下轮 400。"""
    answered = {m.get("tool_call_id") for m in messages if m.get("role") == "tool"}
    for m in messages:
        if m.get("role") == "assistant" and m.get("tool_calls"):
            for tc in m["tool_calls"]:
                cid = tc.get("id", "")
                if cid not in answered:
                    messages.append({"role": "tool", "tool_call_id": cid,
                                     "content": "(上一轮被中断，未执行)"})
                    answered.add(cid)


class Session:
    """多轮会话：跨轮保存 对话历史 / 已确认需求 / 已产模型 / 用户水平。

    交互与教学内核的载体：`send(text)` 多轮；工具经 sessionctx 读写本会话状态。
    """

    def __init__(self, settings: Settings | None = None, system_extra: str = "",
                 goal: str = "", agent: Agent | None = None):
        self.agent = agent or Agent(settings, system_extra=system_extra)
        self.goal = goal or ""
        self.messages: list = [{"role": "system", "content": self.agent._system()}]
        self.meta: dict = {
            "user_level": "unknown",   # unknown / novice / expert
            "requirements": {},        # 已确认需求：key -> {value, source}
            "artifacts": [],           # 已产出的模型/文件
            "turn": 0,
        }
        sessionctx.set_current(self)

    # ---- 会话级状态读写（供工具调用）----
    def set_level(self, level: str) -> None:
        self.meta["user_level"] = str(level or "unknown").strip().lower()

    def remember(self, key: str, value: str, source: str = "user") -> None:
        self.meta["requirements"][str(key)] = {"value": str(value), "source": str(source)}

    def requirements_text(self) -> str:
        reqs = self.meta["requirements"]
        if not reqs:
            return "(尚无已确认需求)"
        return "\n".join(f"- {k}: {v['value']}  〔来源:{v['source']}〕" for k, v in reqs.items())

    def intent_text(self) -> str:
        it = self.meta.get("intent")
        if not it:
            return "(尚未记录建模意图——动手前应先 set_model_intent)"
        return (f"场景：{it['scenario']}\n驱动：{it['driver']}\n"
                f"能量：{it['energy']}\n预判范围：{it['expected']}")

    def batch_text(self) -> str:
        b = self.meta.get("batch")
        if not b:
            return "(未设定批量框架)"
        return (f"基准模型：{b['base_model']}\n扫描变量/范围：{b['vary']}\n"
                f"观察量：{b['observe']}\n工况数：{b.get('cases') or '(待定)'}")

    # ---- 一轮对话 ----
    def send(self, user_text: str) -> Output:
        self.meta["turn"] += 1
        # 目标定档取"会话中出现过的最高复杂度"，避免一直沿用首句模糊需求
        if not self.goal or _RANK[classify_goal(user_text)] > _RANK[classify_goal(self.goal)]:
            self.goal = user_text
        # 把会话级状态注入本轮 user 消息（让模型始终看得到"已确认什么"）
        ctx = (f"【会话状态】第{self.meta['turn']}轮 | 用户水平:{self.meta['user_level']}\n"
               f"【已确认需求】\n{self.requirements_text()}\n"
               f"【建模意图】\n{self.intent_text()}\n"
               f"【批量框架】\n{self.batch_text()}")
        self.messages.append({"role": "user", "content": f"{ctx}\n\n【本轮输入】\n{user_text}"})
        out = Output()
        self.agent._loop(self.messages, out, goal=self.goal)
        # 记录产出：解析工具轨迹里的模型文件
        for t in out.trace:
            if t["tool"] in ("write_file", "edit_file") and isinstance(t.get("args"), dict):
                p = t["args"].get("path")
                if p and p.endswith(".i") and p not in self.meta["artifacts"]:
                    self.meta["artifacts"].append(p)
            if t["tool"] == "run_relap5":
                m = re.search(r"输出=(\S+\.o)", str(t.get("result", "")))
                if m:
                    self.meta["last_o"] = m.group(1)     # 最近一次真跑的 .o（结果表用）
        return out

    # ---- 会话存取（界面多会话历史用） ----
    def state(self) -> dict:
        return {"goal": self.goal, "messages": self.messages, "meta": self.meta}

    def restore(self, st: dict) -> None:
        self.goal = st.get("goal", "")
        self.messages = st.get("messages") or [{"role": "system", "content": self.agent._system()}]
        self.meta = st.get("meta") or {"user_level": "unknown", "requirements": {},
                                       "artifacts": [], "turn": 0}
        sessionctx.set_current(self)

