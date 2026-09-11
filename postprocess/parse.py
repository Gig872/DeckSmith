# -*- coding: utf-8 -*-
"""解析 RELAP5 输出(.o)：抽取各时刻的表（控制体状态 / 接管流量）。

设计要点：
- 先去掉 Fortran 行首控制字符；
- **表头驱动**对列（控制体表列名可能随工况变化，如只有 voidg 没有 voidf）；
- 接管表列序固定，用固定下标；
- 全程容错：解析不出就跳过，不臆造。
返回：{部件号: {变量名: [(时刻, 数值), ...]}}（控制体表、接管表各一份）。
"""
from __future__ import annotations

import re

_CTRL = {" ", "0", "1", "+"}
_TIME = re.compile(r"time=\s*([\d.eE+-]+)")
_ROW = re.compile(r"^\s*(\d{3}-\d{6})\s+(.*)$")
_HDR_VOL = re.compile(r"^\s*Vol\.no\.\s+.*pressure.*$")
_HDR_JUN = re.compile(r"^\s*Jun\.no\..*mass\s+flow.*$")
_ANY_TABLE = re.compile(r"^\s*(Vol\.no\.|Jun\.no\.)")

# 控制体：按表头列名取值
VOL_VARS = ("pressure", "voidf", "voidg", "voidgo", "tempf", "tempg")
# 接管：固定列序（0=接管号 1=来向 2=去向 3=液速 4=汽速 5=质量流量 6=面积）
JUN_VARS = {"liq_vel": 3, "vap_vel": 4, "mass_flow": 5, "area": 6}


def clean_ctrl(text: str) -> str:
    """去掉每行行首的 Fortran 控制字符（一个）。"""
    out = []
    for line in text.split("\n"):
        if line and line[0] in _CTRL:
            out.append(line[1:].rstrip("\r"))
        else:
            out.append(line.rstrip("\r"))
    return "\n".join(out)


def _read_rows(lines: list[str], i: int) -> list[list[str]]:
    """读 i 之后的表数据行，直到下一张表头（**不**跳行，保留中间的时间标记行）。"""
    rows, j = [], i + 1
    while j < len(lines) and not _ANY_TABLE.match(lines[j]):
        if _ROW.match(lines[j]):
            rows.append(lines[j].split())
        j += 1
    return rows


def parse(text: str) -> tuple[dict, dict]:
    """返回 (volumes, junctions)：{id: {var: [(t, val), ...]}}。"""
    lines = clean_ctrl(text).split("\n")
    cur_t = None
    vol: dict[str, dict] = {}
    jun: dict[str, dict] = {}
    i = 0
    while i < len(lines):
        ln = lines[i]
        mt = _TIME.search(ln)
        if mt:
            try:
                cur_t = float(mt.group(1))
            except ValueError:
                pass
        if _HDR_VOL.match(ln):
            names = ln.split()
            rows = _read_rows(lines, i)
            if cur_t is not None:
                for tk in rows:
                    d = vol.setdefault(tk[0], {})
                    for var in VOL_VARS:
                        if var in names:
                            idx = names.index(var)
                            try:
                                d.setdefault(var, []).append((cur_t, float(tk[idx])))
                            except (ValueError, IndexError):
                                pass
            i += 1
            continue
        if _HDR_JUN.match(ln):
            rows = _read_rows(lines, i)
            if cur_t is not None:
                for tk in rows:
                    if len(tk) < 7:
                        continue
                    d = jun.setdefault(tk[0], {})
                    for var, idx in JUN_VARS.items():
                        try:
                            d.setdefault(var, []).append((cur_t, float(tk[idx])))
                        except (ValueError, IndexError):
                            pass
            i += 1
            continue
        i += 1
    return vol, jun


def output_times(vol: dict, jun: dict) -> list[float]:
    ts = set()
    for src in (vol, jun):
        for d in src.values():
            for series in d.values():
                ts.update(t for t, _v in series)
    return sorted(ts)
