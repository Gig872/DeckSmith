# -*- coding: utf-8 -*-
"""自主评估（独立复核）：不靠“专家经验”，用与仿真**无关**的独立路子核对结果。

核心思路（见 skill 70）：把结果对着**物理铁律与独立估算**验，而不是凭感觉。
- 饱和一致性：两相应在 T_sat(p)；单相液不应过热（tempf ≤ T_sat）；单相汽不应过冷。
- 能量平衡：给了功率/流量/入口温度时，ΔT 应与 Q/(ṁ·cp) 同量级。
（守恒/拓扑由 `check_sanity`/`result_summary` 覆盖，两者配合。）
"""
from __future__ import annotations

import math

from registry import tool
import tools.relap5 as _R
from postprocess import extract as _E
from postprocess import water as _W

_SB = _R._SB


def _last(ser: dict, cid: str):
    pts = ser.get(cid)
    return pts[-1][1] if pts else None


@tool("verify_result",
      "**自主评估/独立复核**：用与仿真无关的独立估算核对结果——① 饱和一致性"
      "（两相是否在 T_sat(p)、单相液是否过热、单相汽是否过冷）② 能量平衡"
      "（给 power/mdot/tin 时 ΔT 是否与 Q/(ṁ·cp) 同量级）。返回 通过/存疑/未覆盖 清单。"
      "**凡要下结论/交付，先跑它 + check_sanity，再说话。**",
      {"o_path": {"type": "string"},
       "power": {"type": "number", "description": "加热功率 [W]（可选，做能量平衡用）"},
       "mdot": {"type": "number", "description": "质量流量 [kg/s]（可选；不给则取末态最大接管|质量流量|）"},
       "tin": {"type": "number", "description": "入口温度 [K]（可选；不给则取末态最低 tempf）"},
       "tol_k": {"type": "number", "description": "温度容差 [K]，默认 5"}},
      ["o_path"])
def verify_result(o_path: str, power=None, mdot=None, tin=None, tol_k: float = 5.0) -> str:
    p = _SB.resolve(o_path)
    if not p.is_file():
        return f"[自主评估] 文件不存在: {o_path}"
    text = _R._read_o(p)
    ser_p = _E.get_series(text, "pressure")
    ser_tf = _E.get_series(text, "tempf")
    ser_tg = _E.get_series(text, "tempg")
    ser_vg = _E.get_series(text, "voidg")
    ser_mf = _E.get_series(text, "mass_flow")
    if not ser_p:
        return "[自主评估] 未解析到控制体压力表（这份 .o 可能没有状态表或格式不同）。"

    tol = float(tol_k)

    # ---- 一、饱和一致性 ----
    passed, doubt, uncover = [], [], []
    ids = sorted(set(ser_p) & set(ser_tf)) if ser_tf else sorted(ser_p)
    sat_lines = []
    for cid in ids:
        pi = _last(ser_p, cid)
        tf = _last(ser_tf, cid)
        vg = _last(ser_vg, cid)
        tg = _last(ser_tg, cid)
        ts = _W.sat_temp_K(pi) if pi else float("nan")
        if tf is None or not pi:
            uncover.append(f"{cid}：缺末态压力/温度")
            continue
        if math.isnan(ts):
            uncover.append(f"{cid}：压力 {pi:.3g} Pa 超出估算范围（饱和核对未覆盖）")
            continue
        if vg is None:
            uncover.append(f"{cid}：无 voidg，相态未知（仅给 tempf={tf:.1f}K、Tsat={ts:.1f}K）")
            continue
        if 0.02 < vg < 0.98:                       # 两相
            d = tf - ts
            tag = "✓" if abs(d) <= tol else "⚠ 存疑"
            if abs(d) > tol:
                doubt.append(f"{cid} 两相但 tempf−Tsat={d:+.1f}K（应≈0）")
            else:
                passed.append(f"{cid} 两相 tempf≈Tsat")
            sat_lines.append(f"  · {cid}: p={pi:.4g}Pa→Tsat={ts:.1f}K  voidg={vg:.3g}  "
                             f"tempf={tf:.1f}K（Δ={d:+.1f}）  {tag}")
        elif vg <= 0.02:                            # 单相液：不得过热
            d = ts - tf                              # 过冷度
            tag = "✓ 单相液(过冷)" if d >= -tol else "⚠ 存疑(液过热)"
            if d < -tol:
                doubt.append(f"{cid} 单相液但 tempf 高于 Tsat {(-d):.1f}K（亚稳/不物理）")
            else:
                passed.append(f"{cid} 单相液 过冷 {d:.1f}K")
            sat_lines.append(f"  · {cid}: p={pi:.4g}Pa→Tsat={ts:.1f}K  voidg≈0  "
                             f"tempf={tf:.1f}K（过冷 {d:+.1f}K）  {tag}")
        else:                                       # 单相汽：不得过冷
            tv = tg if tg is not None else tf
            d = tv - ts
            tag = "✓ 单相汽(过热)" if d >= -tol else "⚠ 存疑(汽过冷)"
            if d < -tol:
                doubt.append(f"{cid} 单相汽但温度低于 Tsat {(-d):.1f}K（不物理）")
            else:
                passed.append(f"{cid} 单相汽 过热 {d:.1f}K")
            sat_lines.append(f"  · {cid}: p={pi:.4g}Pa→Tsat={ts:.1f}K  voidg≈1  "
                             f"tempg={tv:.1f}K（过热 {d:+.1f}K）  {tag}")

    cap = 12
    shown = sat_lines[:cap]
    more = f"\n  …（另有 {len(sat_lines) - cap} 个控制体，略）" if len(sat_lines) > cap else ""

    # ---- 二、能量平衡（可选） ----
    energy = ["  未提供 power/mdot/tin，跳过（给齐后可做 ΔT 量级核对）。"]
    if power is not None:
        q = float(power)
        m = float(mdot) if mdot is not None else None
        if m is None and ser_mf:
            vals = [abs(_last(ser_mf, c)) for c in ser_mf if _last(ser_mf, c) is not None]
            m = max(vals) if vals else None
        t_in = float(tin) if tin is not None else (
            min(_last(ser_tf, c) for c in ser_tf if _last(ser_tf, c) is not None) if ser_tf else None)
        t_out = max(_last(ser_tf, c) for c in ser_tf if _last(ser_tf, c) is not None) if ser_tf else None
        if m and t_in is not None and t_out is not None and m > 0:
            cp = _W.cp_liquid(t_in)                     # kJ/kg·K
            dt_exp = q / (m * cp * 1000.0)              # K
            dt_act = t_out - t_in
            rel = abs(dt_act - dt_exp) / dt_exp * 100 if dt_exp else float("inf")
            tag = "✓ 同量级" if rel <= 25 else "⚠ 存疑"
            if rel > 25:
                doubt.append(f"能量平衡：ΔT 实测 {dt_act:.1f}K vs 期望 {dt_exp:.1f}K（偏差 {rel:.0f}%）")
            else:
                passed.append("能量平衡 ΔT 同量级")
            energy = [f"  Q={q:.4g}W, ṁ={m:.4g}kg/s, tin={t_in:.1f}K, cp(tin)={cp:.3f}kJ/kgK",
                      f"  期望 ΔT≈{dt_exp:.1f}K；实测 ΔT={dt_act:.1f}K（出口最高温）；相对偏差 {rel:.0f}%  {tag}"]
        else:
            energy = ["  信息不足（缺流量或温度），能量平衡未覆盖。"]

    # ---- 三、结论 ----
    head = (f"[自主评估] {o_path}（末态；独立复核，非仿真自证）\n"
            f"口径：{_W.notes()}\n")
    lines = [head,
             "一、饱和一致性（最硬的独立检查）", *shown, more,
             "", "二、能量平衡（量级核对）", *energy, "",
             f"三、结论：通过 {len(passed)}，存疑 {len(doubt)}，未覆盖 {len(uncover)}。"]
    if doubt:
        lines.append("⚠ 存疑（必须处理或明确说明，不得当作正确）:")
        lines += [f"    - {d}" for d in doubt]
    if uncover:
        lines.append("○ 未覆盖（补数据后再评）:")
        lines += [f"    - {u}" for u in uncover[:8]]
    if not doubt and passed:
        lines.append("→ 独立检查未发现矛盾；**仍须**与 check_sanity（守恒/拓扑）合看，"
                     "并对安全相关结论留保守裕度。")
    return "\n".join(lines)
