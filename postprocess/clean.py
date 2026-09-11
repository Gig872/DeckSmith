# -*- coding: utf-8 -*-
"""清洗 RELAP5 输出(.o)：去 Fortran 控制字符、压多余空行；抽规模/结束/错误统计。"""
from __future__ import annotations

import re

from .parse import clean_ctrl, parse, output_times

_NORMAL = re.compile(r"Transient terminated|input processing completed successfully")
_FINAL = re.compile(r"Final time=\s*([\d.eE+-]+)")


def clean_text(raw: str) -> str:
    """规范化：逐行去一个控制字符，并把 3+ 连续空行压成 1 个空行。"""
    t = clean_ctrl(raw)
    return re.sub(r"\n{3,}", "\n\n", t)


def error_lines(text: str, n: int = 20) -> list[str]:
    return [ln.strip()[:200] for ln in text.splitlines() if "********" in ln][:n]


def stats(raw: str) -> dict:
    """概览：是否正常结束 / 最终时间 / 错误数 / 编辑数 / 控制体·接管数 / 行数。"""
    t = clean_ctrl(raw)
    vol, jun = parse(raw)   # 传原始文本；parse 自身会清洗一次（勿双洗）
    times = output_times(vol, jun)
    mt = _FINAL.findall(t)
    errs = [ln for ln in t.splitlines() if "********" in ln]
    return {
        "normal_end": bool(_NORMAL.search(t[-4000:])),
        "final_time": (mt[-1] if mt else None),
        "n_errors": len(errs),
        "n_edits": len(times),
        "n_volumes": len(vol),
        "n_junctions": len(jun),
        "lines": t.count("\n") + 1,
    }


def summary_text(raw: str) -> str:
    s = stats(raw)
    ft = f"{s['final_time']} s" if s["final_time"] else "?"
    return (f"正常结束={s['normal_end']}  最终时间={ft}  错误数={s['n_errors']}\n"
            f"编辑数={s['n_edits']}  控制体={s['n_volumes']}  接管={s['n_junctions']}  行数={s['lines']}")
