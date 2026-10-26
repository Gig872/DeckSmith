# -*- coding: utf-8 -*-
"""任务类型族（PLAN.md §3）：T1 从零建模（在 families.py）、T2 改造既有模型、T3 排错修复。

- numerical：数值无关性（控制体数 / 时间步）。
- modify_model (T2)：给一张可运行的卡 + 改造指令 → 真值 = 改造后的卡。
- fix_deck (T3)：给一张有故障的卡 + "跑不起来/结果不对，修好" → 真值 = 干净卡。

T2/T3 **同时挂在"难族"上**（泵回路 / 并联 / 失流 / 破口 / 热构件 / 临界流），
以压出多部件下的语义与拓扑错误。
"""
from __future__ import annotations

import re

from bench.families import FAMILIES, KEY_SINGLE_PIPE, TaskSpec, fmt, heater_pipe

# 各族的一份基准参数（用于 T2 改造与 T3 排错的底卡）
BASE = {
    "single_pipe_steady": {"area": 0.02, "length": 1.0, "nvol": 4, "vertical": False,
                           "mdot": 5.0, "power": 1.0e5},
    "pump_loop": {"head": 20.0, "p_bound": 0.5e6},
    "parallel_channels": {"areaA": 0.001, "areaB": 0.001, "p_out": 0.9e6},
    "lof_transient": {"inertia": 0.2, "trip_time": 5.0, "power": 1.0e5},
    "sbloca_blowdown": {"break_area": 2.0e-4, "p0": 15.0e6, "trip_time": 5.0},
    "hs_gap": {"power": 5.0e4, "gap_p": 1.0e6, "mdot": 0.3},
    "critical_nozzle": {"p0": 5.0e6, "subcool": 20.0, "nozzle_D": 0.113},
    "turbine": {"p_in": 5.0e6, "p_out": 0.5e6, "eff": 0.85},
}


def _deck(family: str, params: dict) -> tuple[str, str, list]:
    return FAMILIES[family][1](params)


def _set_dtmax(deck: str, dt: float) -> str:
    out = []
    for ln in deck.splitlines():
        if ln.strip().startswith("201 "):
            parts = ln.split()
            parts[3] = fmt(dt)
            out.append("  ".join(parts))
        else:
            out.append(ln)
    return "\n".join(out) + "\n"


# ---------------- 数值无关性 ----------------
NPIPE = {"area": 0.02, "length": 1.0, "vertical": False, "mdot": 10.0, "power": 1.0e5}
NVOLS = [4, 8, 16, 32]


def numerical() -> list[TaskSpec]:
    from bench.families import sbloca as sbloca_fn
    out = []
    for i, n in enumerate(NVOLS, 1):
        p = {**NPIPE, "nvol": n}
        deck, nl, key = heater_pipe(p)
        out.append(TaskSpec(f"numerical_grid_{i:03d}", "numerical_grid", p, nl, deck, key))
    base = {"break_area": 2.0e-4, "p0": 15.0e6, "trip_time": 5.0}
    for i, dt in enumerate([0.01, 0.005, 0.001], 1):
        deck, nl, key = sbloca_fn(base)
        deck = _set_dtmax(deck, dt)
        out.append(TaskSpec(f"numerical_dt_{i:03d}", "numerical_dt",
                            {**base, "dtmax": dt}, nl + f" 时间步上限取 {dt:g} s。", deck, key))
    return out


# ---------------- T2 改造既有模型（挂难族） ----------------
# (族, 族内基准, 改的键, 新值, 工程化说法)
MOD_SPECS = [
    ("pump_loop", "head", 40.0, "把泵的额定压头从 20 m 提高到 40 m"),
    ("pump_loop", "p_bound", 0.8e6, "把回路两端边界压力从 0.5 MPa 提高到 0.8 MPa"),
    ("parallel_channels", "areaB", 0.002, "把支路 B 的流通面积从 10 cm2 改为 20 cm2"),
    ("parallel_channels", "p_out", 0.95e6, "把出口定压从 0.9 MPa 改为 0.95 MPa"),
    ("lof_transient", "inertia", 0.5, "把泵的转动惯量从 0.2 增大到 0.5"),
    ("lof_transient", "trip_time", 2.0, "把切泵时刻从 5 s 提前到 2 s"),
    ("lof_transient", "power", 2.0e5, "把加热功率从 100 kW 提高到 200 kW"),
    ("sbloca_blowdown", "break_area", 5.0e-4, "把破口面积从 2e-4 m2 增大到 5e-4 m2"),
    ("sbloca_blowdown", "trip_time", 10.0, "把破口开启时刻从 5 s 推迟到 10 s"),
    ("hs_gap", "power", 8.0e4, "把裂变功率从 50 kW 提高到 80 kW"),
    ("hs_gap", "gap_p", 2.0e6, "把初始间隙压力从 1.0 MPa 提高到 2.0 MPa"),
    ("critical_nozzle", "nozzle_D", 0.299, "把喷管内径从 0.113 m 改为 0.299 m"),
    ("critical_nozzle", "subcool", 50.0, "把上游过冷度从 20 K 提高到 50 K"),
    ("turbine", "eff", 0.70, "把透平等熵效率从 0.85 降到 0.70"),
    ("turbine", "p_out", 0.3e6, "把透平出口背压从 0.5 MPa 降到 0.3 MPa"),
]


def modify() -> list[TaskSpec]:
    out = []
    for k, (fam, key, val, phrase) in enumerate(MOD_SPECS, 1):
        base = dict(BASE[fam])
        base_deck, _nl, key_out = _deck(fam, base)
        newp = {**base, key: val}
        ref_deck, _, _ = _deck(fam, newp)
        ctx = f"case_{k:03d}.i"
        nl = (f"现有输入卡见工作目录的 {ctx}（它已能正常运行，模型结构不要改动）。"
              f"请在此基础上改造：{phrase}；其余设置保持不变。改造后请真跑确认仍能正常结束。")
        out.append(TaskSpec(f"modify_{k:03d}", "modify_model",
                            {**newp, "mod_key": key, "src_family": fam}, nl,
                            ref_deck, key_out, task_type="T2",
                            context_deck=base_deck, context_name=ctx))
    return out


# ---------------- T3 排错修复（挂难族） ----------------
def _f_no_terminator(deck: str) -> str:
    return "\n".join(l for l in deck.splitlines() if l.strip() != ".") + "\n"


def _f_bad_comment(deck: str) -> str:
    return re.sub(r"(?m)^=", "", deck, count=1)


def _f_int_float(deck: str) -> str:
    return re.sub(r"(?m)^(\d{7}\s+1\s+)(\d+)\.0", r"\1\2", deck, count=1)


def _f_bad_pointer(deck: str) -> str:
    return re.sub(r"(?m)^(\d{7}\s+)(\d{3})(\d{2})(0000)(\s)", r"\g<1>\g<2>99\g<4>\g<5>",
                  deck, count=1)


def _f_raise_pressure(deck: str) -> str:
    """静默故障：把最后一个定压边界压力抬到 3 倍（仍能跑，但物理不合理）。"""
    ms = list(re.finditer(r"(?m)^(\d{7}\s+0\.0\s+)([\d.]+e-?\d+)", deck))
    if not ms:
        return deck
    m = ms[-1]
    p = float(m.group(2)) * 3.0
    e = int(__import__("math").floor(__import__("math").log10(abs(p))))
    mant = p / (10.0 ** e)
    return deck[:m.start(2)] + f"{mant:.1f}e{e}" + deck[m.end(2):]


FAULTS = [
    ("no_terminator", "缺少终止卡", _f_no_terminator),
    ("bad_comment", "注释行未以 * 或 = 开头", _f_bad_comment),
    ("int_float", "浮点字段写成了整数", _f_int_float),
    ("bad_pointer", "接管指针指向了不存在的控制体", _f_bad_pointer),
    ("raise_pressure", "某个定压边界压力被抬高（能跑但物理不合理）", _f_raise_pressure),
]
FIX_ON = ["single_pipe_steady", "pump_loop", "parallel_channels", "lof_transient",
          "sbloca_blowdown", "hs_gap"]


def fixbed() -> list[TaskSpec]:
    out, k = [], 0
    for fam in FIX_ON:
        clean, _nl, key = _deck(fam, dict(BASE[fam]))
        for name, desc, fn in FAULTS:
            k += 1
            broken = fn(clean)
            if broken == clean:
                continue                      # 该族不适用此故障，跳过
            ctx = f"broken_{k:02d}.i"
            nl = (f"工作目录里的 {ctx} 是别人写的一张 RELAP5 输入卡，但它有问题"
                  f"（可能跑不起来，也可能能跑但结果不对，原因不一定如描述）。"
                  f"请诊断故障、给出修正后的输入卡，并真跑确认：正常结束、物理自洽。")
            out.append(TaskSpec(f"fixdeck_{k:03d}", "fix_deck",
                                {"fault": name, "fault_desc": desc, "src_family": fam},
                                nl, clean, key, task_type="T3",
                                context_deck=broken, context_name=ctx))
    return out


TT_FAMILIES = {
    "numerical": numerical,
    "modify_model": modify,
    "fix_deck": fixbed,
}
