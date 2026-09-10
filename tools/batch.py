# -*- coding: utf-8 -*-
"""批量仿真：按参数化模板生成若干输入卡，逐个真跑，汇总结果（含守恒校验）。

用法：模板里用 {{参数名}} 占位；vary 给出每个参数的取值列表；工具做笛卡尔积，
逐个渲染→真跑→校验→汇总成表，并写 CSV 到 workspace/batch/。
"""
from __future__ import annotations

import csv
import json
import re
from itertools import product
from pathlib import Path

from registry import tool
import tools.relap5 as R

_SB = R._SB
_BATCH = _SB.root / "batch"


def _render(tmpl: str, combo: dict) -> str:
    s = tmpl
    for k, v in combo.items():
        s = re.sub(r"\{\{\s*" + re.escape(str(k)) + r"\s*\}\}", str(v), s)
    return s


def _as_vary(vary) -> list[dict]:
    if isinstance(vary, str):
        vary = json.loads(vary)
    out = []
    for item in vary or []:
        if isinstance(item, dict) and "name" in item:
            vals = item.get("values")
            if isinstance(vals, str):
                vals = [x.strip() for x in vals.split(",") if x.strip()]
            out.append({"name": item["name"], "values": list(vals or [])})
    return out


def _run_case(rel_i: str, timeout: int):
    """真跑一个工况，取回 (正常结束, 质量误差%, 压力范围, 温度范围, 首条错误, o路径)。"""
    msg = R.run_relap5(rel_i, timeout=timeout)
    ok = "正常结束=True" in msg
    m = re.search(r"输出=(\S+)", msg)
    o = m.group(1).replace("\\", "/") if m else None
    mass = pr = tr = err = vmax = mj = ""
    if o:
        s = R.check_sanity(o)
        mm = re.search(r"质量误差≈([\d.eE+-]+).*?占比\s*([-\d.]+%)", s)
        if mm:
            mass = mm.group(2)
        pp = re.search(r"压力范围:\s*(\S+\s*~\s*\S+)", s)
        if pp:
            pr = pp.group(1)
        tt = re.search(r"温度范围:\s*(\S+\s*~\s*\S+)", s)
        if tt:
            tr = tt.group(1)
        # 两相关键量：最大空泡份额（烧干判据 void→1）
        try:
            idx, vrows = R._final_state(R._clean(R._read_o(R._SB.resolve(o))))
            j = idx.get("voidg")
            if j is not None and vrows:
                vals = []
                for tk in vrows:
                    try:
                        vals.append(float(tk[j]))
                    except (ValueError, IndexError):
                        pass
                if vals:
                    vmax = round(max(vals), 3)
        except Exception:  # noqa: BLE001
            pass
        # 最大接管质量流量（壅塞/破口流量的观测量；|ṁ| 最大者）
        try:
            jrows = R._final_junctions(R._clean(R._read_o(R._SB.resolve(o))))
            fs = []
            for tk in jrows:
                try:
                    fs.append(abs(float(tk[5])))
                except (ValueError, IndexError):
                    pass
            if fs:
                mj = round(max(fs), 4)
        except Exception:  # noqa: BLE001
            pass
        if not ok:                       # 失败工况：带上首条错误，省得再去翻 .o
            errs = R._errors(R._clean(R._read_o(R._SB.resolve(o))))
            if errs:
                err = errs[0].lstrip("*").strip()[:80]
    return ok, mass, pr, tr, vmax, mj, err, o


@tool("batch_sim",
      "参数化批量仿真：给参数化模板(用 {{名}} 占位)+各参数取值列表，自动生成全部工况、逐个真跑、"
      "校验并汇总成表。每工况给出 正常结束/质量误差/**voidg_max**（最大空泡份额，烧干判据）/**mj_max**"
      "（最大接管质量流量，壅塞/破口流量观测用）/**烧干?**/温度范围；CSV 另含各工况 .o 路径（可深看）。",
      {"template": {"type": "string", "description": "工作目录内的参数化 .i 路径（含 {{参数}} 占位）"},
       "vary": {"type": "array", "description": "参数列表：[{name, values:[...]}]；values 也可给逗号分隔字符串",
                "items": {"type": "object"}},
       "max_cases": {"type": "integer", "description": "工况上限，默认 20，超了拒绝"},
       "timeout": {"type": "integer", "description": "单工况超时秒，默认 120"}},
      ["template", "vary"])
def batch_sim(template: str, vary, max_cases: int = 20, timeout: int = 120) -> str:
    try:
        vars_ = _as_vary(vary)
    except Exception as e:  # noqa: BLE001
        return f"[batch] vary 解析失败: {e}（应为 [{{\"name\":..,\"values\":[..]}}]）"
    if not vars_ or any(not v["values"] for v in vars_):
        return "[batch] 需要每个参数都给出非空取值列表：[{name, values:[...]}]"
    ip = _SB.resolve(template)
    if not ip.is_file():
        return f"[batch] 模板不存在: {template}"
    tmpl = ip.read_text(encoding="utf-8")
    names = [v["name"] for v in vars_]
    missing = [n for n in names if "{{" not in tmpl or n not in tmpl]
    if missing:
        return f"[batch] 模板里找不到占位 {missing}（模板需含 {{{{参数名}}}}）"

    combos = [dict(zip(names, p)) for p in product(*[v["values"] for v in vars_])]
    if len(combos) > int(max_cases):
        return (f"[batch] 将生成 {len(combos)} 个工况，超过上限 {max_cases}。"
                "请收窄取值/减少参数，或显式调大 max_cases。")

    _BATCH.mkdir(parents=True, exist_ok=True)
    rows = []
    for i, combo in enumerate(combos, 1):
        content = _render(tmpl, combo)
        sub = _BATCH / f"{ip.stem}_c{i:03d}.i"
        sub.write_text(content, encoding="utf-8")
        rel = str(sub.relative_to(_SB.root)).replace("\\", "/")
        ok, mass, pr, tr, vmax, mj, err, o = _run_case(rel, timeout)
        dry = "是" if (vmax != "" and float(vmax) >= 0.99) else ""
        row = dict(combo)
        row.update({"正常结束": ok, "质量误差": mass, "压力范围": pr, "温度范围": tr,
                    "voidg_max": vmax, "voidg≈1": dry, "mj_max": mj, "错误(首条)": err, "o": o or ""})
        rows.append(row)

    # 汇总表
    cols = names + ["正常结束", "质量误差", "voidg_max", "mj_max", "voidg≈1"]
    show_err = any(not r["正常结束"] for r in rows)
    if show_err:
        cols.append("错误(首条)")
    lines = ["[batch_sim] 工况数=%d  模板=%s" % (len(rows), template),
             "  " + " | ".join(cols)]
    for r in rows:
        lines.append("  " + " | ".join(str(r.get(c, "")) for c in cols))
    nfail = sum(1 for r in rows if not r["正常结束"])
    ndry = sum(1 for r in rows if r["voidg≈1"] == "是")
    lines.append(f"小结：正常结束 {len(rows)-nfail}/{len(rows)}，失败 {nfail}，"
                 f"voidg_max≥0.99 的工况 {ndry}。"
                 "（每工况均做了守恒/量级校验；每工况 .o 路径见 CSV 的 o 列，可用 result_summary 深看）")

    csv_path = _BATCH / f"{ip.stem}_summary.csv"
    try:
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.DictWriter(f, fieldnames=names +
                               ["正常结束", "质量误差", "压力范围", "温度范围", "voidg_max",
                                "mj_max", "voidg≈1", "错误(首条)", "o"])
            w.writeheader()
            w.writerows(rows)
        lines.append("汇总已写: " + str(csv_path.relative_to(_SB.root)).replace("\\", "/"))
    except OSError as e:
        lines.append(f"(CSV 写入失败: {e})")
    return "\n".join(lines)
