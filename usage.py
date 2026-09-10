# -*- coding: utf-8 -*-
"""用量/计费统计：累计 token（输入/输出）与估算花费。

价格表为**示例值**，可在界面里改（存 config.json 的 prices）；币种随模型标注。
"""
from __future__ import annotations

from dataclasses import dataclass, field

# 每 100 万 token 单价 (输入, 输出, 币种)。示例值，务必按你的实际计费改。
DEFAULT_PRICES: dict[str, tuple[float, float, str]] = {
    "deepseek-chat": (2.0, 8.0, "CNY"),
    "deepseek-reasoner": (4.0, 16.0, "CNY"),
    "deepseek-v4-flash": (2.0, 8.0, "CNY"),
    "deepseek-v4": (2.0, 8.0, "CNY"),
    "gpt-4o": (2.5, 10.0, "USD"),
    "gpt-4o-mini": (0.15, 0.6, "USD"),
    "qwen-plus": (0.8, 2.0, "CNY"),
    "glm-4": (1.0, 1.0, "CNY"),
    "moonshot-v1-8k": (12.0, 12.0, "CNY"),
    "claude-3-5-sonnet": (3.0, 15.0, "USD"),
    "claude-3-5-haiku": (0.8, 4.0, "USD"),
}


def price_of(model: str, prices: dict | None = None) -> tuple[float, float, str]:
    """查模型单价；找不到就退化为 (0,0,'?')（只统计 token，不估花费）。"""
    tbl = {**DEFAULT_PRICES, **(prices or {})}
    m = (model or "").lower()
    if m in tbl:
        return tuple(tbl[m])  # type: ignore[return-value]
    for k, v in tbl.items():          # 前缀匹配（如 deepseek-v4-flash-xxx）
        if m.startswith(k):
            return tuple(v)  # type: ignore[return-value]
    return (0.0, 0.0, "?")


@dataclass
class Usage:
    calls: int = 0
    tokens_in: int = 0
    tokens_out: int = 0
    cost: float = 0.0
    currency: str = "?"
    last_in: int = 0
    last_out: int = 0
    by_model: dict = field(default_factory=dict)   # model -> [calls, in, out, cost]

    def add(self, usage: dict, model: str, prices: dict | None = None) -> None:
        """累加一次调用的用量。usage 形如 {prompt_tokens, completion_tokens, total_tokens}。"""
        if not usage:
            return
        ti = int(usage.get("prompt_tokens") or 0)
        to = int(usage.get("completion_tokens") or 0)
        if not ti and not to:
            tot = int(usage.get("total_tokens") or 0)
            ti = tot
        self.calls += 1
        self.tokens_in += ti
        self.tokens_out += to
        self.last_in, self.last_out = ti, to
        pin, pout, cur = price_of(model, prices)
        if cur != "?":
            self.currency = cur
        self.cost += ti / 1e6 * pin + to / 1e6 * pout
        row = self.by_model.setdefault(model, [0, 0, 0, 0.0])
        row[0] += 1
        row[1] += ti
        row[2] += to
        row[3] += ti / 1e6 * pin + to / 1e6 * pout

    def summary(self, model: str = "", prices: dict | None = None) -> str:
        pin, pout, cur = price_of(model, prices)
        cur = cur if cur != "?" else self.currency
        lines = [
            f"调用次数：{self.calls}",
            f"输入 token：{self.tokens_in:,}   输出 token：{self.tokens_out:,}",
            f"合计 token：{self.tokens_in + self.tokens_out:,}",
            f"本模型单价(每 1M)：入 {pin} / 出 {pout} {cur if cur != '?' else ''}",
            f"累计花费≈ {self.cost:.4f} {cur if cur != '?' else '(未计)'}",
        ]
        if len(self.by_model) > 1:
            lines.append("— 分模型 —")
            for m, (c, ti, to, co) in self.by_model.items():
                lines.append(f"  {m}: {c} 次, 入{ti:,}/出{to:,}, ≈{co:.4f}")
        return "\n".join(lines)

    def reset(self) -> None:
        self.calls = self.tokens_in = self.tokens_out = 0
        self.cost = 0.0
        self.last_in = self.last_out = 0
        self.by_model.clear()

    def to_dict(self) -> dict:
        return {"calls": self.calls, "tokens_in": self.tokens_in, "tokens_out": self.tokens_out,
                "cost": self.cost, "currency": self.currency, "by_model": self.by_model}

    def load(self, d: dict) -> None:
        self.reset()
        if not d:
            return
        self.calls = int(d.get("calls", 0))
        self.tokens_in = int(d.get("tokens_in", 0))
        self.tokens_out = int(d.get("tokens_out", 0))
        self.cost = float(d.get("cost", 0.0))
        self.currency = d.get("currency", "?")
        self.by_model = d.get("by_model", {}) or {}
