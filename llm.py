# -*- coding: utf-8 -*-
"""OpenAI 兼容 LLM 客户端：支持 tools(function calling)，零第三方依赖。
dry_run=True 时用脚本化 mock，便于离线验证 agent 循环。"""
from __future__ import annotations

import json
import time
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


# 额度不足的识别特征（各家措辞不同，逐家实测后补齐）：
#   DeepSeek / Moonshot：402 + "Insufficient Balance"
#   DashScope（阿里，Qwen/Kimi 走兼容模式）：403 + "Free quota exhausted ... add funds"
#     ⚠ 这两句不含 "insufficient"/"exceeded your current quota"，漏判会被当成普通异常
#       记为 crashed=True，直接把 R_exec/R_phys/R_sem 打脏——跨模型评测必须先覆盖。
_CREDIT_HINTS = ("insufficient balance", "insufficient_quota", "exceeded your current quota",
                 "you exceeded your current quota", "余额不足", "欠费", "billing",
                 "account balance", "credit",
                 "quota exhausted", "free quota", "add funds",
                 "arrearage", "recharge")


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
        # 各家接口的私有参数（如 Qwen3 的 enable_thinking）：由配置原样并入
        if getattr(self.s, "extra_body", None):
            payload.update(self.s.extra_body)
        # DeepSeek v4 系列：默认思考会吃掉正文，故默认关思考走正文；可在设置里开"思考模式"
        if "v4" in self.s.model:
            if getattr(self.s, "thinking", False):
                payload["thinking"] = {"type": "enabled"}     # 开启思维链
            else:
                payload["thinking"] = {"type": "disabled"}
                payload["reasoning_effort"] = "low"

        url = self.s.base_url.rstrip("/") + "/chat/completions"
        data = json.dumps(_sanitize(payload)).encode("utf-8")

        # 限流重试：Moonshot Tier0 只有 3 RPM，单个 agent 任务会连续快速发请求，
        # 突发必然触发 429。若不重试，一次 429 会被 harness 记成 crashed=True，
        # 直接污染 R_exec/R_phys/R_sem——这是实验环境问题，不是能力问题。
        # 只对 429（限流）重试；402/403 欠费与 400 参数错误仍立即抛出。
        _max_retry = int(getattr(self.s, "rate_limit_retries", 8) or 8)
        for _attempt in range(_max_retry + 1):
            req = urllib.request.Request(url, data=data, method="POST")
            req.add_header("Content-Type", "application/json")
            req.add_header("Authorization", "Bearer " + self.s.api_key)
            try:
                with urllib.request.urlopen(req, timeout=self.s.request_timeout) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
                break
            except urllib.error.HTTPError as e:
                raw = e.read().decode('utf-8', 'replace')
                low = raw.lower()
                if e.code == 429 and not _is_out_of_credit(e.code, raw):
                    if _attempt >= _max_retry:
                        raise LLMError(f"HTTP 429 限流重试 {_max_retry} 次仍失败: {raw[:200]}")
                    # 优先用响应头里的重置时间，否则指数退避（1,2,4,…封顶 30 s）
                    _wait = 0.0
                    try:
                        _reset = e.headers.get("X-RateLimit-Reset")
                        if _reset:
                            _wait = max(0.0, float(_reset))
                    except Exception:  # noqa: BLE001
                        _wait = 0.0
                    if _wait <= 0:
                        _wait = min(30.0, 2.0 ** _attempt)
                    _wait += 0.3          # 少量抖动，避免多 worker 同时重试
                    self.last_retry_wait = _wait
                    time.sleep(_wait)
                    continue
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
