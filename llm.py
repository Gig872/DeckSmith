# -*- coding: utf-8 -*-
"""OpenAI 兼容 LLM 客户端：支持 tools(function calling)，零第三方依赖。
dry_run=True 时用脚本化 mock，便于离线验证 agent 循环。"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

from config import Settings


class LLMError(RuntimeError):
    pass


class OutOfCredit(LLMError):
    """API 额度／余额不足。

    必须与普通错误区别对待：**立即截断整批运行**，且不得把受影响的任务
    记为失败（那是实验环境问题，不是被测系统的能力问题）。"""
    pass


# 额度不足的识别特征（DeepSeek 返回 402 + Insufficient Balance；各家措辞略有不同）
_CREDIT_HINTS = ("insufficient balance", "insufficient_quota", "exceeded your current quota",
                 "you exceeded your current quota", "余额不足", "欠费", "billing",
                 "account balance", "credit")


def _is_out_of_credit(code: int, raw: str) -> bool:
    if code == 402:                      # Payment Required：明确欠费
        return True
    low = (raw or "").lower()            # 429 等：只有措辞命中"余额/额度"才算
    return any(h in low for h in _CREDIT_HINTS)


def _sanitize(o):
    if isinstance(o, dict):
        return {k: _sanitize(v) for k, v in o.items()}
    if isinstance(o, list):
        return [_sanitize(x) for x in o]
    if isinstance(o, str):
        return o.encode("utf-8", "replace").decode("utf-8")
    return o


class LLM:
    def __init__(self, settings: Settings):
        self.s = settings
        self._mock_step = 0  # dry_run 用
        self.last_usage: dict = {}   # 最近一次调用的 usage（供预算统计）

    def complete(self, messages: list[dict], tools: list[dict] | None = None) -> dict:
        """返回 assistant message: {content, tool_calls?, reasoning_content?}。"""
        if self.s.dry_run:
            return self._mock(tools)
        payload = {
            "model": self.s.model,
            "messages": messages,
            "temperature": self.s.temperature,
            "max_tokens": self.s.max_tokens,
        }
        if tools:
            payload["tools"] = tools
        # DeepSeek v4 系列：默认思考会吃掉正文，故默认关思考走正文；可在设置里开"思考模式"
        if "v4" in self.s.model:
            if getattr(self.s, "thinking", False):
                payload["thinking"] = {"type": "enabled"}     # 开启思维链
            else:
                payload["thinking"] = {"type": "disabled"}
                payload["reasoning_effort"] = "low"

        url = self.s.base_url.rstrip("/") + "/chat/completions"
        data = json.dumps(_sanitize(payload)).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Authorization", "Bearer " + self.s.api_key)
        try:
            with urllib.request.urlopen(req, timeout=self.s.request_timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            raw = e.read().decode('utf-8', 'replace')
            if _is_out_of_credit(e.code, raw):
                raise OutOfCredit(f"HTTP {e.code}: {raw[:400]}")
            raise LLMError(f"HTTP {e.code}: {raw[:400]}")
        except urllib.error.URLError as e:
            raise LLMError(f"网络错误: {e.reason}")
        self.last_usage = body.get("usage") or {}
        ch = body["choices"][0]
        msg = ch.get("message") or {}
        if not (msg.get("content") or msg.get("tool_calls")):
            raise LLMError("空回复（可能被思考占满或过滤）")
        # **截断保护**：finish_reason=length 表示被 max_tokens 截断。
        # 若此时**没有 tool_calls**，核心循环（core._loop 的 `if not calls: break`）会把它
        # 当成"最终答复"而**静默收尾**（实测：台架 FIX-II 试点 a1 输出了 5.7 万字符的退化
        # 重复文本、零工具调用，却被记为正常结束）。故显式报错，绝不当作成功。
        if ch.get("finish_reason") == "length" and not msg.get("tool_calls"):
            raise LLMError("输出被 max_tokens 截断（finish_reason=length）且无工具调用；"
                           "不得视为最终答复——请缩短单次输出或改用分块/生成器式构建")
        return msg

    # ---- dry_run mock：先调一次工具（避开 ask_user 以免阻塞），再给最终答复 ----
    def _mock(self, tools: list[dict] | None) -> dict:
        self._mock_step += 1
        if tools and self._mock_step == 1:
            names = [t["function"]["name"] for t in tools]
            pick = next((n for n in names if n != "ask_user"), names[0] if names else "")
            return {"content": "", "tool_calls": [{
                "id": "call_mock_1", "type": "function",
                "function": {"name": pick, "arguments": "{}"},
            }]}
        return {"content": "[dry-run] 已根据工具结果完成（mock 答复）。"}


def list_models(base_url: str, api_key: str, timeout: int = 15) -> list[str]:
    """向 OpenAI 兼容接口查询可用模型（GET {base_url}/models），返回模型 id 列表。"""
    url = (base_url or "").rstrip("/") + "/models"
    req = urllib.request.Request(url, method="GET")
    req.add_header("Authorization", "Bearer " + (api_key or ""))
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            body = json.loads(resp.read().decode("utf-8", "replace"))
    except urllib.error.HTTPError as e:
        raise LLMError(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:200]}")
    except urllib.error.URLError as e:
        raise LLMError(f"网络错误: {e.reason}")
    data = body.get("data") or body.get("models") or []
    ids = []
    for it in data:
        if isinstance(it, dict) and it.get("id"):
            ids.append(str(it["id"]))
        elif isinstance(it, str):
            ids.append(it)
    return sorted(set(ids))
