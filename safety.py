# -*- coding: utf-8 -*-
"""熔断 + 预算 + 沙箱：防死循环空转、防越界。

Guard  : 步数 / 时长 / token / 无进展（连续相同工具调用）→ 触发即终止。
Budget : **目标自适应预算**——按用户最终目标的复杂度起档（保守），
         运行中只在"确有进展且无空转"时逐级放宽；硬顶不可逾越。
Sandbox: 工具读写限定在工作目录内（越界拒绝）。
"""
from __future__ import annotations

import hashlib
import json
import re
import time
from pathlib import Path

from config import Settings


class Breaker(RuntimeError):
    """熔断触发。"""


# ======================= 目标自适应预算 =======================
#
# 四个维度：steps(工具轮次) / seconds(墙钟秒) / tokens(累计 token) / ctx(上下文字符上限)
# 起档值来自 GOAL_TIERS（保守）；硬顶来自 Settings（不可逾越）。
# 标定参照：最复杂的目标形态——完整整体式压水堆(PWR)、长时瞬态、
#   含点堆动力学/控制系统/停堆/一二次回路。硬顶按此留足，
#   但起档给得小，靠"苛刻升级"逐步放开，避免一上来就烧钱。
GOAL_TIERS: dict[str, dict[str, int]] = {
    "S":  {"steps": 25,  "seconds": 300,  "tokens": 800_000,    "ctx": 160_000},
    "M":  {"steps": 45,  "seconds": 900,  "tokens": 1_500_000,  "ctx": 240_000},
    "L":  {"steps": 80,  "seconds": 1800, "tokens": 3_000_000,  "ctx": 320_000},
    "XL": {"steps": 200, "seconds": 5400, "tokens": 20_000_000, "ctx": 600_000},
}
_TIER_ORDER = ["S", "M", "L", "XL"]

# 目标复杂度信号词（小写匹配）
_XL_KW = ["整体", "完整", "全厂", "一二回路", "一回路", "二回路", "压水堆", "pwr",
          "一体化", "全系统", "多回路", "点堆", "停堆", "安注", "稳压器",
          "蒸汽发生器", "控制系统", "瞬态", "全厂断电", "断电事故", "破口", "loca"]
_L_KW = ["回路", "系统", "多个", "多部件", "管道", "接管", "阀门", "泵", "热构件",
         "环路", "组件", "排错", "瞬态起步", "学习新", "新部件", "新类型"]
_S_KW = ["最小", "单个", "单一", "简单", "仅", "仅仅", "基础", "入门", "读格式",
         "怎么写", "小样例"]
# 批量/参数扫描类：一次要生成并跑多个工况，天然多轮 → 起档别抠
_BATCH_KW = ["批量", "一批", "扫描", "参数化", "敏感性", "全自动", "参数研究", "工况范围"]
_COMPONENTS = ["pipe", "branch", "snglvol", "sngljun", "tmdpvol", "tmdpjun",
               "valve", "pump", "accum", "separatr", "turbine", "heat",
               "annulus", "mtpljun", "eccmix", "jetmixer"]


def classify_goal(goal: str) -> str:
    """按目标文本给复杂度起档（确定性、零成本）。返回 S/M/L/XL。"""
    g = (goal or "").lower()
    if not g.strip():
        return "M"                       # 未知目标 → 取中档，别太抠
    score = 0
    xl = sum(1 for k in _XL_KW if k in g)
    l = sum(1 for k in _L_KW if k in g)
    s = sum(1 for k in _S_KW if k in g)
    comps = sum(1 for c in _COMPONENTS if c in g)
    score += 4 if xl else 0
    score += min(3, xl)
    score += min(3, l)
    score += 3 if comps >= 5 else 2 if comps >= 3 else 1 if comps >= 2 else 0
    score -= 2 if (s and not xl) else 0
    score += 1 if len(g) > 120 else 0
    score += 3 if any(k in g for k in _BATCH_KW) else 0   # 批量/扫描类：天然多轮，别抠
    if score <= 0:      # 明确"最小/单一"或单部件 → 最省
        return "S"
    if score <= 2:      # 2~3 部件、中等组合
        return "M"
    if score <= 4:      # 多部件/系统级、需学新类型
        return "L"
    return "XL"         # 整回路/整堆/瞬态+控制+停堆


class Budget:
    """目标自适应预算：起档保守，苛刻升级，硬顶封死。"""

    def __init__(self, goal: str, s: Settings):
        self.tier = classify_goal(goal)
        # 硬顶：不可逾越（来自 Settings；默认按"最复杂目标形态"标定）
        self.hard = {
            "steps": int(getattr(s, "max_steps", 200) or 200),
            "seconds": int(getattr(s, "max_seconds", 5400) or 5400),
            "tokens": int(getattr(s, "token_budget", 12_000_000) or 12_000_000),
            "ctx": int(getattr(s, "ctx_chars", 600_000) or 600_000),
        }
        # 起档值不得超过硬顶
        self.cur = {d: min(v, self.hard[d]) for d, v in GOAL_TIERS[self.tier].items()}
        # 升级控制（苛刻）。XL 也留升级余地：token 维度常先于步数打满，
        # 若一上来就锁死在硬顶，大任务会被 token 上限"半途截断"（实测踩过）。
        self.max_ups = {"S": 3, "M": 3, "L": 2, "XL": 2}[self.tier]
        self.ups = 0
        self.cooldown = 8            # 两次升级至少间隔的步数
        self.prog_window = 12        # 进展必须发生在最近这么多步内
        self.factor = 1.5            # 每次只放宽 50%
        self._last_up_step = 0
        # 进展证据
        self.ever_progress = False   # 是否出现过真实进展（跑通/报错减少）
        self.last_progress_step = 0
        self.err_best: int | None = None
        self.log: list[str] = []

    def snapshot(self) -> dict:
        return dict(self.cur)


class Guard:
    def __init__(self, s: Settings, goal: str = ""):
        self.s = s
        self.t0 = time.time()
        self.tokens = 0
        self.ctx_peak = 0
        self._last_sig = None
        self._same = 0
        self._last_tool = None
        self._tool_streak = 0
        self.tool_streak_cap = 6   # 同一工具连续调用上限（防同类空转）
        self._healthy = True       # 无空转信号
        self.budget = Budget(goal, s)

    # ---- 熔断检查（用自适应预算的当前上限）----
    def tick(self, step: int) -> None:
        cur = self.budget.cur
        if step > cur["steps"]:
            raise Breaker(f"步数超过上限 {cur['steps']}")
        if time.time() - self.t0 > cur["seconds"]:
            raise Breaker(f"超时(>{cur['seconds']}s)")
        if self.tokens > cur["tokens"]:
            raise Breaker(f"token 超过预算 {cur['tokens']}")

    def note_calls(self, calls: list[dict]) -> None:
        """无进展检测：连续两轮完全相同的工具调用 → 熔断。"""
        sig = hashlib.md5(json.dumps(calls, sort_keys=True, ensure_ascii=False).encode()).hexdigest()
        self._same = self._same + 1 if sig == self._last_sig else 0
        self._last_sig = sig
        self._healthy = self._healthy and self._same < 1
        if self._same >= 2:
            raise Breaker("无进展：连续相同的工具调用，疑似死循环")

    def note_tool(self, name: str) -> None:
        """同一工具连续调用过多（即使参数不同）→ 熔断，防"反复查/反复试"空转。"""
        self._tool_streak = self._tool_streak + 1 if name == self._last_tool else 0
        self._last_tool = name
        self._healthy = self._healthy and self._tool_streak < 2
        if self._tool_streak >= self.tool_streak_cap:
            raise Breaker(f"同一工具 {name} 连续调用 {self._tool_streak + 1} 次，疑似空转——请改变策略")

    # ---- 进展观测：喂给预算 ----
    def observe(self, step: int, tool: str, result: str) -> None:
        b = self.budget
        if tool == "run_relap5" and "正常结束=True" in result:
            # 能把卡跑到"正常结束"本身就是一个里程碑（输入处理通过、瞬态开跑）
            b.ever_progress = True
            b.last_progress_step = step
        elif tool == "parse_output":
            m = re.search(r"错误数=(\d+)", result)
            if m:
                n = int(m.group(1))
                # 首次量到 / 报错切实减少 / 已 0 错 → 进展
                if b.err_best is None or n < b.err_best or n == 0:
                    b.ever_progress = True
                    b.last_progress_step = step
                if b.err_best is None or n < b.err_best:
                    b.err_best = n
        elif tool in ("write_file", "edit_file") and b.ever_progress:
            if "已写入" in result or "已替换" in result:
                b.last_progress_step = step   # 编辑只刷新"近期"，不单独算进展

    # ---- 苛刻升级 ----
    def maybe_grow(self, step: int) -> str:
        """仅在"有真实进展 + 无空转 + 近期"时，把接近上限的维度放宽一档。"""
        b = self.budget
        if not self._healthy:                     # 有空转迹象：冻结，绝不放宽
            return ""
        if b.ups >= b.max_ups:                    # 升级次数用尽
            return ""
        if step - b._last_up_step < b.cooldown:   # 冷却期
            return ""
        if not b.ever_progress:                   # 从未有过真实进展：不许放宽
            return ""
        if step - b.last_progress_step > b.prog_window:  # 进展不新鲜：不许放宽
            return ""
        stressed = []
        if step >= 0.8 * b.cur["steps"]:
            stressed.append("steps")
        if (time.time() - self.t0) >= 0.8 * b.cur["seconds"]:
            stressed.append("seconds")
        if self.tokens >= 0.8 * b.cur["tokens"]:
            stressed.append("tokens")
        if self.ctx_peak >= 0.8 * b.cur["ctx"]:
            stressed.append("ctx")
        if not stressed:                          # 没接近上限，不必放宽
            return ""
        grew = []
        for d in stressed:
            new = min(b.hard[d], int(b.cur[d] * b.factor) + 1)
            if new > b.cur[d]:
                b.cur[d] = new
                grew.append(f"{d}:{new}")
        if not grew:
            return ""
        b.ups += 1
        b._last_up_step = step
        msg = f"[预算放宽 第{b.ups}/{b.max_ups}次] " + ", ".join(grew)
        b.log.append(msg)
        return msg


class Sandbox:
    def __init__(self, root: str):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)

    def resolve(self, path: str) -> Path:
        p = Path(path)
        full = (self.root / p).resolve() if not p.is_absolute() else p.resolve()
        try:
            full.relative_to(self.root)
        except ValueError:
            raise Breaker(f"沙箱拒绝：越界路径 {path}")
        return full
