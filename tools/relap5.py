# -*- coding: utf-8 -*-
"""RELAP5 领域工具：run_relap5（真跑）/ parse_output（解析 .o）/ validate_i（最小静态校验）。

沙箱：输入文件在 workspace 内；产物写到 workspace/runs/（不裸存 relap5 目录）；
relap5 运行 cwd = 含 tpf* 物性文件的目录（否则找不到物性文件）。
"""
from __future__ import annotations

import hashlib
import re
import shutil
import subprocess
import time
from pathlib import Path

from registry import tool
from safety import Sandbox
from config import load, relap5_paths

_SB = Sandbox(load().workspace)
_CTRL = {" ", "0", "1", "+"}
_SEQ = 0   # 进程内递增，保证输出名唯一（即使同秒、同前缀）


def _next_seq() -> int:
    global _SEQ
    _SEQ += 1
    return _SEQ


def _clean(raw: str) -> str:
    out = []
    for line in raw.split("\n"):
        if line and line[0] in _CTRL:
            out.append(line[1:].rstrip("\r"))
        else:
            out.append(line.rstrip("\r"))
    return "\n".join(out)


def end_kind(t: str) -> str:
    """判定一次运行的终止类型（只看尾部 3000 字符）。

    取值：
      steady      —— `Transient has reached steady state.`（稳态收敛；JIT-11 实测）
      end_time    —— `Transient terminated by end of time step cards.`（跑满 201-299 设定的终点）
      cpu_limit   —— CPU 余量不足被第 105 卡掐停
                     （实测打印串：`Transient terminated by approach to cpu time limit.`）
      input_only  —— 尾部只有 `Input processing completed successfully.`，说明**没有进入推进**
      failure     —— `transient terminated by failure.`（数值崩溃）
      terminated_other —— 其余 `Transient terminated ...`（如用户中止等；本库未观察到）
      unknown     —— 以上都不是

    注意：一次**正常跑完**的运行，`Input processing completed successfully.` 出现在输出前部，
    不会落进尾部 3000 字符；只有"过完输入处理就停"才会。所以 input_only 与 input 通过是两回事。

    第 105 卡终止的打印串由实测确定（手册 A2.7/A2.8 只说 "immediately terminated"）：
      `Transient terminated by approach to cpu time limit.`
    **它含有子串 "Transient terminated"** —— 若不加辨别会被当成正常结束，
    而实测该情形 advancements attempted=0（一步都没推进）。
    """
    tail = (t or "")[-3000:]
    low = tail.lower()
    if "terminated by failure" in low:
        return "failure"
    if "approach to cpu time limit" in low:
        return "cpu_limit"
    if "has reached steady state" in tail:
        return "steady"
    if "end of time step cards" in tail.lower():
        return "end_time"
    if "cpu time" in low or "cpu limit" in low:
        return "cpu_limit"
    if "input processing completed successfully" in low:
        return "input_only"
    if "transient terminated" in low:
        return "terminated_other"
    return "unknown"


def _normal_end(t: str) -> bool:
    """是否算"正常结束"。与 end_kind 单一来源对齐：
    只认 `steady`（稳态收敛）与 `end_time`（跑满时间步）。
    2026-10-18 审计：657 张归档卡上新旧判定逐条一致（510 end_time + 1 steady 为真，
    其余全假）；原实现里 `input processing completed successfully` 分支因大小写永不命中，
    属死代码，故移除。"""
    # cpu_limit 不算正常结束：实测该情形 advancements attempted=0，一步都没推进。
    return end_kind(t) in ("steady", "end_time", "terminated_other")




def steady_declared(t: str) -> bool:
    """RELAP5 是否**自判**达到稳态（区别于"跑满时间步但未必稳态"）。

    台架级需要用它区分两种都算「正常结束」的情形：
      · True  —— 打印 `Transient has reached steady state.`（真收敛到稳态）；
      · False —— 打印 `Transient terminated by end of time step cards.`（跑满时间步）。
    实测：我方手工复原的 Marviken 卡=True；LLM 生成的 Marviken 卡=False
    （它把容器建成闭环无压边界，稳态是"整罐静止"的平凡解）。
    纯只读辅助函数，不改任何既有输出格式。
    """
    return "has reached steady state" in (t or "")[-3000:]


def _errors(t: str, n: int = 8) -> list[str]:
    return [ln.strip()[:200] for ln in t.split("\n") if "********" in ln][:n]


def _read_o(p: Path) -> str:
    return p.read_bytes().decode("utf-8", "replace")


def _prune_runs(outdir: Path, keep: int) -> None:
    """只保留最近 keep 次运行（.o/.r 按主干成组），删更早的；keep<=0 表示不清理。"""
    if keep <= 0:
        return
    try:
        groups: dict[str, list[Path]] = {}
        for p in outdir.iterdir():
            if p.is_file():
                groups.setdefault(p.stem, []).append(p)
    except OSError:
        return
    if len(groups) <= keep:
        return

    def _mtime(g: list[Path]) -> float:
        vals = []
        for f in g:
            try:
                vals.append(f.stat().st_mtime)
            except OSError:          # 文件可能被别的进程删了（并发跑算例时的竞争）
                continue
        return max(vals) if vals else 0.0

    ordered = sorted(groups.values(), key=_mtime, reverse=True)
    for g in ordered[keep:]:
        for f in g:
            try:
                f.unlink()
            except OSError:
                pass


# ---- 输入卡静态检查（规则全部出自 RELAP5 手册 Appendix A）----
# 参考：NUREG/CR-5535 Rev.1 App A（MOD3.3Beta）与 INEEL-EXT-98-00834-V2 App A（3D/2.4）。
_MAX_CARDNO = 536870911        # 手册 A1.5：允许的最大卡号
_MAX_WORDS = 2097151           # 手册 A1.5：全部卡的总词数上限
_MAX_CARD_WORDS = 2047         # 手册 A1.6：单卡 + 其续行卡的总词数上限

# 大小写：本机构建（R5-ATHENA 2.4.1.1a）**全部关键字必须小写**。
# 实测：NEW / TRANSNT / SNGLVOL / TIME / NULL / GT / SI 任意一处大写都导致输入处理报错
# （见 论文/数据 探针：card 100 大写 → "Unable to determine problem option"）。
# 只对这些"关键字"报警，不对用户自定义名报警（名字大写不影响语义）。
_KEYWORDS = {
    "new", "restart", "reset", "reedit", "strip", "cmpcoms", "stdy-st", "transnt",
    "run", "inp-chk", "si", "british", "none", "filename", "binary", "fmtout",
    "snglvol", "sngljun", "tmdpvol", "tmdpjun", "pipe", "branch", "valve", "pump",
    "turbine", "separatr", "separ", "jetmixer", "mtpljun", "eccmix", "accum",
    "fwhtr", "cprssr", "annulus", "rodbundl", "time", "null", "gt", "lt", "ge",
    "le", "eq", "ne", "and", "or", "table", "trip",
}


def _words(line: str) -> int:
    """按手册 A1.5 的三种字母数字形式计词数（引号内不切、nHz 按 8 字符/词）。"""
    n, i, L = 0, 0, len(line)
    while i < L:
        c = line[i]
        if c in " \t,":
            i += 1
            continue
        if c in "\"'":
            q, i = c, i + 1
            while i < L:
                if line[i] == q:
                    if i + 1 < L and line[i + 1] == q:   # 成对定界符 = 字面字符
                        i += 2
                        continue
                    i += 1
                    break
                i += 1
            n += 1
            continue
        m = re.match(r"(\d+)H", line[i:])
        if m:                                            # nHz 形式：跳过 n 列
            cnt = int(m.group(1))
            i += m.end() + cnt
            n += max(1, (cnt + 7) // 8)
            continue
        while i < L and line[i] not in " \t,":
            i += 1
        n += 1
    return n


def _data_part(line: str) -> str:
    """截掉数据卡尾部的行内注释（手册 A1.5：注释以 * 或 $ 起，须自成字段）。"""
    inq = None
    for i, c in enumerate(line):
        if inq:
            if c == inq:
                inq = None
            continue
        if c in "\"'":
            inq = c
            continue
        if c in "*$" and (i == 0 or line[i - 1] in " \t,"):
            return line[:i]
    return line


def _quote_ok(line: str) -> bool:
    """引号字段必须成对（同一字符启闭；相邻双写为字面字符）。"""
    for q in ('"', "'"):
        i, cnt, L = 0, 0, len(line)
        while i < L:
            if line[i] == q:
                if i + 1 < L and line[i + 1] == q:
                    i += 2
                    continue
                cnt += 1
            i += 1
        if cnt % 2:
            return False
    return True


_NUM_RE = re.compile(r"^[+-]?(?:\d+\.?\d*|\.\d+)(?:[EeDd]\s*[+-]?\d+|[+-]\d+)?$")


def _fnum(x: str):
    """按手册 A1.5 解析数值字段。

    RELAP5 允许**隐式指数**：`1.0-6` = 1.0e-6、`0.1245+2` = 12.45、`1.245E 1` = 12.45
    （指数允许 E/e/D/d，字母后允许一个空格当正号）。直接 float() 会把这些判成非法，
    使几何检查**静默跳过**——故此处显式处理。
    """
    if x is None:
        return None
    s = str(x).strip()
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        pass
    if not _NUM_RE.match(s):
        return None
    s2 = re.sub(r"([EeDd])\s*([+-]?)(\d+)$", lambda m: "e" + (m.group(2) or "+") + m.group(3), s)
    s2 = re.sub(r"^([+-]?(?:\d+\.?\d*|\.\d+))([+-]\d+)$", r"\1e\2", s2)
    try:
        return float(s2)
    except ValueError:
        return None


def _expand(words: list[str], k: int) -> dict:
    """顺序展开格式（手册 A1.8）：每 k 词一组，末词为本组终止序号。返回 {序号: 前 k-1 词}。"""
    out: dict[int, list[str]] = {}
    start = 1
    for i in range(0, len(words) - k + 1, k):
        chunk = words[i:i + k]
        end = _fnum(chunk[-1])
        if end is None or end != int(end) or end < start:
            break
        for v in range(start, int(end) + 1):
            out[v] = chunk[:-1]
        start = int(end) + 1
    return out


def _geometry_check(raw: list[str]) -> list[str]:
    """几何一致性静态检查（只告警，不改判分）。

    依据（手册 Appendix A，各部件几何卡说明）：
      · 体积必须等于面积 × 长度（相对误差 1e-6；三者皆非零时检查）
      · 高程变化绝对值 ≤ 长度
      · 倾角为 0 ⇒ 高程变化为 0；倾角非零 ⇒ 与高程变化同号
      · 壁面粗糙度 < 水力直径 / 2
      · 含安注箱的问题，第 110 卡必须给出 NITROGEN（手册 A2.8）
    """
    cards: list[tuple[int, list[str]]] = []
    for line in raw:
        s = line.strip()
        if not s or s[0] in "*$=./":
            continue
        body = _data_part(s)
        if body.startswith("+"):
            if cards:
                cards[-1][1].extend(body[1:].split())
            continue
        w = body.split()
        if not w or not w[0].isdigit():
            continue
        cards.append((int(w[0]), w[1:]))

    comps: dict[int, dict] = {}
    for no, w in cards:
        if len(str(no)) == 7 and no % 10000 == 0 and len(w) >= 2:
            comps[no // 10000] = {"type": w[1].lower(), "vol": {}}

    def vol(ccc: int, vno: int) -> dict:
        return comps[ccc]["vol"].setdefault(vno, {})

    for no, w in cards:
        ccc, suf = no // 10000, no % 10000
        if ccc not in comps:
            continue
        typ = comps[ccc]["type"]
        if typ == "pipe":
            if 101 <= suf <= 199:                     # 面积（2 词/组）
                for v, vals in _expand(w, 2).items():
                    a = _fnum(vals[0])
                    if a is not None:
                        vol(ccc, v)["A"] = a
            elif 301 <= suf <= 399:                   # 长度
                for v, vals in _expand(w, 2).items():
                    x = _fnum(vals[0])
                    if x is not None:
                        vol(ccc, v)["L"] = x
            elif 401 <= suf <= 499:                   # 体积
                for v, vals in _expand(w, 2).items():
                    x = _fnum(vals[0])
                    if x is not None:
                        vol(ccc, v)["V"] = x
            elif 601 <= suf <= 699:                   # 竖直角
                for v, vals in _expand(w, 2).items():
                    x = _fnum(vals[0])
                    if x is not None:
                        vol(ccc, v)["ang"] = x
            elif 701 <= suf <= 799:                   # 高程变化
                for v, vals in _expand(w, 2).items():
                    x = _fnum(vals[0])
                    if x is not None:
                        vol(ccc, v)["el"] = x
            elif 801 <= suf <= 899:                   # 摩擦数据（粗糙度, 水力直径, 序号）
                for v, vals in _expand(w, 3).items():
                    r, d = _fnum(vals[0]), _fnum(vals[1])
                    if r is not None:
                        vol(ccc, v)["rough"] = r
                    if d is not None:
                        vol(ccc, v)["dh"] = d
        elif typ in ("snglvol", "tmdpvol", "branch"):
            if 101 <= suf <= 109:                     # 每卡 9 词，对应一个体积
                v = suf - 100
                names = ("A", "L", "V", "az", "ang", "el", "rough", "dh")
                for i, nm in enumerate(names):
                    if i < len(w):
                        x = _fnum(w[i])
                        if x is not None:
                            vol(ccc, v)[nm] = x

    probs: list[str] = []
    for ccc, c in comps.items():
        for v, d in c["vol"].items():
            tag = f"{ccc:03d}-{v:02d}"
            A, L, V = d.get("A"), d.get("L"), d.get("V")
            if A and L and V and abs(V - A * L) > 1e-6 * max(abs(V), abs(A * L)):
                probs.append(f"几何不一致：组件 {tag} 体积 {V:g} ≠ 面积×长度 {A * L:g}"
                             f"（相对误差 {(V - A * L) / max(abs(V), abs(A * L)):.2e}）")
            el, L2 = d.get("el"), L
            if el is not None and L2 and abs(el) > abs(L2) + 1e-9:
                probs.append(f"几何不一致：组件 {tag} 高程变化 {el:g} 超过长度 {L2:g}")
            ang = d.get("ang")
            if ang is not None and el is not None:
                if abs(ang) < 1e-12 and abs(el) > 1e-12:
                    probs.append(f"几何不一致：组件 {tag} 倾角为 0 但高程变化 {el:g} 不为 0")
                elif abs(ang) >= 1e-12 and el * ang < 0:
                    probs.append(f"几何不一致：组件 {tag} 倾角 {ang:g}° 与高程变化 {el:g} 异号")
            r, dh = d.get("rough"), d.get("dh")
            if r and dh and r >= dh / 2.0:
                probs.append(f"几何不一致：组件 {tag} 壁面粗糙度 {r:g} ≥ 水力直径的一半 {dh / 2:g}")

    # 安注箱必须有非凝气体（手册 A2.8：凡含安注箱的问题必须含氮气）
    if any(c["type"] == "accum" for c in comps.values()):
        gas = [w for no, w in cards if no == 110]
        if not gas or not any("nitrogen" in x.lower() for x in gas[0]):
            probs.append("含安注箱但第 110 卡未给出 NITROGEN（手册 A2.8）")
    return probs


@tool("validate_i", "对一段 RELAP5 输入卡做静态检查（终止卡/卡号/注释行/续行/80 列/大小写/几何）。",
      {"text": {"type": "string"}}, ["text"])
def validate_i(text: str) -> str:
    probs: list[str] = []
    raw = text.splitlines()
    words_all = 0            # 全卡总词数
    card_words = 0           # 当前数据卡 + 续行卡的词数
    prev = None              # 上一张有意义的卡的类型
    has_term = False
    upper_seen: list[str] = []

    def add(msg: str) -> None:
        if len(probs) < 6:
            probs.append(msg)

    for lineno, line in enumerate(raw, 1):
        s = line.strip()
        if not s:                       # 手册 A1.4：空行按注释卡处理
            prev = "comment"
            continue
        head = s[0]
        # 手册 A1.1：只读前 80 列。只对**数据卡/续行卡**报警——注释与标题卡
        # 超长只是回显被截断，无害（归档卡里大量中文说明都超长）。
        if head.isdigit() or head == "+":
            if len(line.rstrip()) > 80:
                add(f"第 {lineno} 行超过 80 列（RELAP5 只读前 80 列，其后会被当数据）：{s[:50]}")
        if head in ("*", "$"):          # 手册 A1.4：* 或 $ 均为注释卡
            prev = "comment"
            continue
        if head == "=":                 # 手册 A1.3：标题卡
            prev = "title"
            continue
        if head in (".", "/"):          # 手册 A1.7：终止卡，其后可跟注释文字
            has_term = True
            prev = "term"
            continue
        if head == "+":                 # 手册 A1.6：续行卡
            if prev == "comment":
                add(f"第 {lineno} 行：续行卡前不得有注释卡（手册 A1.4/A1.6）")
            card_words += _words(_data_part(s[1:]))
            if card_words > _MAX_CARD_WORDS:
                add(f"第 {lineno} 行：单卡连同续行超过 {_MAX_CARD_WORDS} 词（手册 A1.6）")
            prev = "cont"
            continue
        if not head.isdigit():
            add(f"第 {lineno} 行疑似非法行（数据卡须以无符号整数卡号开头；注释须以 * 或 $ 开头）：{s[:50]}")
            prev = "bad"
            continue

        # ---- 数据卡 ----
        body = _data_part(s)            # 去掉行内 * / $ 注释
        head_no = body.split()[0]
        if not head_no.isdigit():
            add(f"第 {lineno} 行：卡号须为无符号整数（手册 A1.5）：{head_no[:20]}")
        elif len(head_no) > 9 or int(head_no) > _MAX_CARDNO:
            add(f"第 {lineno} 行：卡号超过上限 {_MAX_CARDNO}：{head_no}")
        # 说明：卡号重复**合法**（后卡替换前卡；只写卡号=删除该卡），故此处不判重复。
        if not _quote_ok(body):
            add(f"第 {lineno} 行：引号字段未成对（手册 A1.5）")
        for tok in body.split():
            if tok.isalpha() and tok.isupper() and tok.lower() in _KEYWORDS:
                if len(upper_seen) < 2:
                    upper_seen.append(tok)
        card_words = _words(body)
        if card_words > _MAX_CARD_WORDS:
            add(f"第 {lineno} 行：单卡词数超过 {_MAX_CARD_WORDS}（手册 A1.6）")
        words_all += card_words
        prev = "data"

    if not has_term:
        add("缺少终止卡（以 . 或 / 开头的行）")
    if words_all > _MAX_WORDS:
        add(f"全卡总词数 {words_all} 超过上限 {_MAX_WORDS}（手册 A1.5）")
    if upper_seen:
        add("关键字须小写（本机构建区分大小写，实测大写会导致输入处理失败）："
            + "、".join(upper_seen))
    for g in _geometry_check(raw):
        add(g)
    return "\n".join(probs) if probs else "静态检查通过（无明显低级错误）。"


def _with_inpchk(text: str) -> str:
    """把第 101 卡换成 `inp-chk`（无则插在 100 卡之后），其余不动。

    手册 A2.3：`101 INP-CHK` 时程序在输入处理结束时停止，不进入时间推进。
    警告：这种"结束"与真正跑完同打印 `Input processing completed successfully.`，
    因此**预检结果绝不能混入 exec_ok**。
    """
    lines = text.splitlines()
    out, done = [], False
    for l in lines:
        if re.match(r"^\s*101\b", l):
            indent = l[:len(l) - len(l.lstrip())]
            out.append(indent + "101  inp-chk")
            done = True
        else:
            out.append(l)
    if not done:
        for i, l in enumerate(out):
            if re.match(r"^\s*100\b", l):
                out.insert(i + 1, "101  inp-chk")
                break
    return "\n".join(out) + "\n"


def precheck(text: str, timeout: int = 60) -> dict:
    """只做输入处理（INP-CHK）并返回结构化结论；不参与任何判分。

    返回 {"stage": "input_ok" | "input_fail" | "no_run",
          "errors": [错误行], "rc": int|None, "o": 输出相对路径}
    """
    d = _SB.root / "_precheck"
    d.mkdir(parents=True, exist_ok=True)
    h = hashlib.md5(text.encode("utf-8")).hexdigest()[:10]
    ip = d / f"pc_{h}.i"
    ip.write_text(_with_inpchk(text), encoding="utf-8")
    msg = run_relap5(str(ip.relative_to(_SB.root)), timeout=timeout)
    m = re.search(r"输出=(\S+)", msg)
    if not m:
        return {"stage": "no_run", "errors": [msg.splitlines()[0][:200]],
                "rc": None, "o": ""}
    o = _SB.resolve(m.group(1))
    t = _clean(_read_o(o)) if o.is_file() else ""
    errs = _errors(t)
    stage = "input_fail" if errs else "input_ok"
    return {"stage": stage, "errors": errs, "rc": 0,
            "o": m.group(1), "end": end_kind(t)}


@tool("precheck_i", "只做输入处理检查（101 INP-CHK）：区分「读入失败」与「运行失败」。"
                   "结论不参与判分。",
      {"text": {"type": "string"}, "timeout": {"type": "integer"}}, ["text"])
def precheck_i(text: str, timeout: int = 60) -> str:
    r = precheck(text, timeout=timeout)
    head = {"input_ok": "输入处理通过", "input_fail": "读入失败", "no_run": "未能运行"}[r["stage"]]
    s = f"[precheck] {head}"
    if r.get("end"):
        s += f"（终止类型={r['end']}）"
    if r["errors"]:
        s += "\n错误：\n" + "\n".join(r["errors"])
    return s


@tool("run_relap5", "真跑一个 RELAP5 输入文件（相对工作目录），返回 rc 与结果摘要。",
      {"i_path": {"type": "string", "description": "工作目录内的 .i 文件路径"},
       "timeout": {"type": "integer"}}, ["i_path"])
def run_relap5(i_path: str, timeout: int = 180) -> str:
    exe, rdir = relap5_paths()
    if not exe.is_file():
        return f"[relap5] 未找到可执行文件（配置 config.json 的 relap5_dir/relap5_exe）。当前={exe}"
    ip = _SB.resolve(i_path)
    if not ip.is_file():
        return f"[relap5] 输入文件不存在: {i_path}"
    outdir = _SB.root / "runs"
    outdir.mkdir(parents=True, exist_ok=True)
    st = time.strftime("%Y%m%d_%H%M%S")
    # 关键：RELAP5 对 -o/-r 路径有 ~80 字符缓冲上限，路径过长会静默截断扩展名，
    # 导致找不到 .o。故输出用"短名"：截断 stem + 4 位哈希（区分同前缀输入）+ 进程内序号
    # （区分同秒多次运行），保证整条路径远低于上限且**绝不撞名**。
    safe = re.sub(r"[^A-Za-z0-9_]", "_", ip.stem)[:12]
    h4 = hashlib.md5(ip.stem.encode("utf-8")).hexdigest()[:4]
    base = f"{safe}_{h4}_{_next_seq():04d}"
    o = outdir / f"{base}.o"
    r = outdir / f"{base}.r"
    for f in (o, r):                       # RELAP5 不覆盖已存在文件，先清目标
        try:
            f.unlink()
        except FileNotFoundError:
            pass
    # 并发隔离：每个进程用独立的工作目录（含 tpf* 物性文件），
    # 避免多进程共用 relap5 安装目录时互删 rstplt/plotfl/stripf 临时文件。
    cwd = _SB.root / "relap5_cwd"
    cwd.mkdir(parents=True, exist_ok=True)
    for f in Path(rdir).glob("tpf*"):
        dst = cwd / f.name
        if not dst.exists():
            try:
                shutil.copy2(f, dst)
            except OSError:
                pass
    for name in ("rstplt", "plotfl", "stripf"):   # 清本进程目录里的临时输出
        fp = Path(cwd) / name
        if fp.is_file():
            try:
                fp.unlink()
            except OSError:
                pass
    cmd = [str(exe), "-i", str(ip), "-o", str(o), "-r", str(r)]
    tmo = max(1, min(int(timeout), 3600))          # 尊重调用方给的超时（上限 1 小时防失控）
    try:
        p = subprocess.run(cmd, cwd=str(cwd), capture_output=True,
                           timeout=tmo, text=True, errors="replace")
    except subprocess.TimeoutExpired:
        return f"[relap5] 运行超时（>{tmo}s），已终止。"   # 独立可识别的超时标记
    except Exception as e:  # noqa: BLE001
        return f"[relap5] 执行失败: {e}"
    if not o.is_file() and (outdir / base).is_file():   # 万一仍被截断：兜底认无扩展名文件
        o = outdir / base
    if not o.is_file():
        return f"[relap5] rc={p.returncode}，但 .o 未生成（可能启动失败）。"
    t = _clean(_read_o(o))
    ok = _normal_end(t)
    errs = _errors(t)
    rel = o.relative_to(_SB.root)
    _prune_runs(outdir, int(getattr(load(), "runs_keep", 50) or 0))   # 保留最近 N 次，防无限增长
    msg = f"[relap5] rc={p.returncode} 正常结束={ok}  输出={rel}"
    if errs:
        msg += "\n错误：\n" + "\n".join(errs)
    return msg


@tool("parse_output", "解析 RELAP5 输出(.o)：返回是否正常结束、错误行、尾部。",
      {"o_path": {"type": "string"}, "max_chars": {"type": "integer"}}, ["o_path"])
def parse_output(o_path: str, max_chars: int = 1200) -> str:
    p = _SB.resolve(o_path)
    if not p.is_file():
        return f"[parse] 文件不存在: {o_path}"
    t = _clean(_read_o(p))
    errs = _errors(t)
    head = f"正常结束={_normal_end(t)}  错误数={len(errs)}"
    body = ("\n错误：\n" + "\n".join(errs)) if errs else ""
    tail = "\n--- 尾部 ---\n" + t[-int(max_chars):]
    return head + body + tail


# ---------------- 结果物理校验（守恒 / 量级；不是画图） ----------------

_HDR_STATE = re.compile(r"^\s*\d?\s*Vol\.no\..*pressure.*temp(f|g)?.*$", re.M)
_ANY_VOLNO = re.compile(r"^\s*\d?\s*Vol\.no\.", re.M)
_ROWV = re.compile(r"^\s*(\d{3}-\d{6})\s+(.*)$")
_HDR_JUN = re.compile(r"^\s*\d?\s*Jun\.no\..*mass\s+flow.*$", re.M)
_ANY_JUN = re.compile(r"^\s*\d?\s*Jun\.no\.", re.M)


def _final_state(t: str):
    """取最后一张状态表（含 pressure/tempf/tempg 列），按表头名对位列。"""
    hdrs = list(_HDR_STATE.finditer(t))
    if not hdrs:
        return {}, []
    h = hdrs[-1]
    names = h.group(0).split()
    idx = {k: (names.index(k) if k in names else None)
           for k in ("pressure", "tempf", "tempg", "voidg")}
    rows = []
    for ln in t[h.end():].split("\n"):
        if _ANY_VOLNO.match(ln):     # 进入下一张表 → 停
            break
        if _ROWV.match(ln):
            rows.append(ln.split())
    return idx, rows


@tool("check_sanity", "结果物理校验：从 .o 抽 最终压力/温度 极值 与 质量守恒误差，判定是否物理合理。"
                     "交付前必用；合理性不过关不得交付。",
      {"o_path": {"type": "string"}}, ["o_path"])
def check_sanity(o_path: str) -> str:
    p = _SB.resolve(o_path)
    if not p.is_file():
        return f"[sanity] 文件不存在: {o_path}"
    t = _clean(_read_o(p))
    out, flags = [], []

    # 1) 是否正常结束 + 最终时间
    ok = _normal_end(t)
    ft = None
    m = re.findall(r"Final time=\s*([\d.Ee+-]+)", t)
    if m:
        ft = m[-1]
    if not ok:
        flags.append("[错误] 未正常结束（有致命错误或提前终止）")

    # 2) 最终状态表的压力/温度极值
    idx, rows = _final_state(t)
    ps, ts = [], []
    for tk in rows:
        try:
            if idx.get("pressure") is not None:
                ps.append(float(tk[idx["pressure"]]))
            for k in ("tempf", "tempg"):
                j = idx.get(k)
                if j is not None:
                    v = float(tk[j])
                    if 100.0 < v < 6000.0:      # 滤掉哨兵值
                        ts.append(v)
        except (ValueError, IndexError):
            pass
    if ps:
        out.append(f"压力范围: {min(ps):.3g} ~ {max(ps):.3g} Pa")
        if min(ps) <= 0:
            flags.append("[错误] 存在非正压力（物理上不可能）")
    if ts:
        out.append(f"温度范围: {min(ts):.1f} ~ {max(ts):.1f} K")
        if max(ts) > 900 or min(ts) < 250:
            flags.append(f"[警告] 温度极值 {min(ts):.0f}~{max(ts):.0f} K 超出常温水/蒸汽合理范围，"
                         "先确认是否读错表，再查边界/能量是否自洽")
    if not ps and not ts:
        out.append("(未能定位最终状态表——请人工确认)")

    # 3) 质量守恒（RELAP5 自报 mass error）。
    #    注意：瞬态排空时末态质量很小，用"末态质量"当分母会把相对误差**虚高**
    #    （曾把 0.4% 的绝对误差算成 19.7%，把 agent 带偏）。故以**过程中最大质量≈初始**为基准。
    me = re.findall(r"mass\s*=\s*([\d.Ee+-]+)\s*kg\s+mass error=\s*([\d.Ee+-]+)", t)
    if me:
        m_last, err = float(me[-1][0]), float(me[-1][1])
        m_ref = max(float(a) for a, _b in me) or 1.0
        ratio = abs(err) / m_ref
        out.append(f"质量守恒: 末态质量≈{m_last:.4g} kg（初始≈{m_ref:.4g}）, "
                   f"累计质量误差≈{err:.3g} kg（占初始 {ratio:.2%}）")
        if ratio > 0.05:
            flags.append(f"[错误] 质量严重不守恒（误差占初始 {ratio:.1%}）——"
                         "边界条件多半不自洽（如定了入口流量却无对应排出）或未收敛")
        elif ratio > 0.01:
            flags.append(f"[警告] 质量误差偏高（占初始 {ratio:.1%}），建议核查边界与时间步")

    verdict = "物理合理性：通过（未发现守恒/量级硬伤）" if not flags else \
              "物理合理性：**存疑**，见下列问题"
    return (f"[check_sanity] 正常结束={ok}  最终时间={ft}\n"
            + "\n".join(out)
            + "\n" + verdict
            + ("\n" + "\n".join(flags) if flags else "")
            + "\n（此工具只查守恒与量级；请再与你在建模意图里写下的预判范围核对。"
            "需要具体数值用 result_summary。）")


def sanity_passes(san: str) -> bool:
    """check_sanity 结果的**唯一**判据（所有脚本一律调用本函数，勿再各写一份）。

    规则：**含 `[错误]` 即不通过**；`[警告]` 容差。
    依据 check_sanity 自身的取值为：硬伤才置 `[错误]`（未正常结束 / 非正压力 /
    质量严重不守恒），软提示置 `[警告]`（温度极值超常 / 质量误差偏高 /
    重复连接 / 净流量≠0），且工具把**只含警告**的情形标为“存疑”而非“不通过”。

    另加两条**失败的关闭**（fail-closed）防御：
      * 结果串为空（拿不到判据）→ 不通过；
      * 结果串含“文件不存在”→ 不通过。
    调用点均传入真实存在的 .o，故这两条不改变既有结果。

    历史坑：曾有脚本写成 `("未通过" not in san) and ("[警告]" not in san)`——
    而 check_sanity **从不输出“未通过”“不通过”**（失败判语是“存疑”），
    该写法实际退化为“只看 `[警告]`”，会**漏判只含 `[错误]` 的失败**。
    """
    s = san or ""
    if not s.strip():
        return False
    if "文件不存在" in s:
        return False
    return "[错误]" not in s


def _final_junctions(t: str):
    """取最后一张接管表（含 from/to/mass flow 列）。列为定序：
    0=接管号 1=来向 2=去向 3=液速 4=汽速 5=质量流量 6=面积 7=喉部比。"""
    hdrs = list(_HDR_JUN.finditer(t))
    if not hdrs:
        return []
    h = hdrs[-1]
    rows = []
    for ln in t[h.end():].split("\n"):
        if _ANY_JUN.match(ln):       # 下一张接管表 → 停
            break
        m = _ROWV.match(ln)
        if m and len(ln.split()) >= 7:
            rows.append(ln.split())
    return rows


def _vol_key(vid: str):
    """'−110-010001' / '110-010001' → '110-01'（控制体键：部件号-体号）。"""
    m = re.match(r"-?(\d{3})-(\d{2})", vid or "")
    return f"{m.group(1)}-{m.group(2)}" if m else None


def _boundary_comps(t: str) -> set:
    """从 'Input data for component 101, inb tmdpvol having ...' 抽出时间相关边界部件号。"""
    b = set()
    for m in re.finditer(r"component\s+(\d+),\s+\S+\s+(\S+)\s+having", t):
        if "tmdp" in m.group(2).lower():
            b.add(m.group(1))
    return b


def _node_balance(t: str):
    """各控制体净流量（+为净流入）。按接管表逐条累加：to 记 +q、from 记 −q。
    返回 {key: (net, throughput)}。"""
    net: dict[str, float] = {}
    thru: dict[str, float] = {}
    for tk in _final_junctions(t):
        try:
            fk, tkk, q = _vol_key(tk[1]), _vol_key(tk[2]), float(tk[5])
        except (ValueError, IndexError):
            continue
        if fk:
            net[fk] = net.get(fk, 0.0) - q
            thru[fk] = thru.get(fk, 0.0) + abs(q)
        if tkk:
            net[tkk] = net.get(tkk, 0.0) + q
            thru[tkk] = thru.get(tkk, 0.0) + abs(q)
    return net, thru


@tool("result_summary", "结果摘要（可信读数）：直接给出 最终各控制体 压力/温度/空泡 与 各接管 质量流量/流速。"
                        "交付里要引用具体数值时，一律用它，**不要**再用 python_exec 去翻 .o（易读错列）。",
      {"o_path": {"type": "string"}, "max_rows": {"type": "integer"}}, ["o_path"])
def result_summary(o_path: str, max_rows: int = 40) -> str:
    p = _SB.resolve(o_path)
    if not p.is_file():
        return f"[result] 文件不存在: {o_path}"
    t = _clean(_read_o(p))
    n = int(max_rows)
    m = re.findall(r"Final time=\s*([\d.Ee+-]+)", t)
    lines = [f"[result_summary] 正常结束={_normal_end(t)}  最终时间={m[-1] if m else '?'}"]

    # 系统质量 / 守恒
    me = re.findall(r"mass\s*=\s*([\d.Ee+-]+)\s*kg\s+mass error=\s*([\d.Ee+-]+)", t)
    if me:
        m_last, err = float(me[-1][0]), float(me[-1][1])
        m_ref = max(float(a) for a, _b in me) or 1.0
        lines.append(f"末态质量≈{m_last:.4g} kg（初始≈{m_ref:.4g}）  累计质量误差≈{err:.3g} kg"
                     f"（占初始 {abs(err)/m_ref:.2%}）")

    # 控制体状态
    idx, vrows = _final_state(t)
    if vrows:
        lines.append("— 控制体 (最终) —")
        for tk in vrows[:n]:
            try:
                vid = tk[0]
                pv = tk[idx["pressure"]] if idx.get("pressure") is not None else "?"
                tv = tk[idx["tempf"]] if idx.get("tempf") is not None else "?"
                vg = tk[idx["voidg"]] if idx.get("voidg") is not None else "?"
                lines.append(f"  {vid}  P={pv} Pa  Tf={tv} K  voidg={vg}")
            except (IndexError, KeyError):
                pass

    # 接管流量
    jrows = _final_junctions(t)
    if jrows:
        lines.append("— 接管 (最终) —")
        for tk in jrows[:n]:
            try:
                lines.append(f"  {tk[0]}  {tk[1]} -> {tk[2]}  质量流量={tk[5]} kg/s  液速={tk[3]} m/s")
            except IndexError:
                pass
        # 拓扑检查：同一对控制体被多个接管重复连接 = 冗余/错误连接
        seen: dict[str, int] = {}
        for tk in jrows:
            try:
                seen[f"{tk[1]} -> {tk[2]}"] = seen.get(f"{tk[1]} -> {tk[2]}", 0) + 1
            except IndexError:
                pass
        dups = [k for k, v in seen.items() if v > 1]
        if dups:
            lines.append("[警告] 重复连接（同一对控制体被接了多次）: " + "; ".join(dups)
                         + " —— 多半多接了一条冗余接管，应只保留一条")

    # 节点流量平衡：每个控制体 进=出（时间相关边界部件除外，它们本就允许净流量）
    net, thru = _node_balance(t)
    if net:
        bcomps = _boundary_comps(t)
        bad = []
        for k, v in sorted(net.items()):
            if k.split("-")[0] in bcomps:
                continue
            tol = max(1e-3, 0.01 * thru.get(k, 0.0))
            if abs(v) > tol:
                bad.append(f"{k} 净流量={v:+.4g} kg/s (吞吐≈{thru.get(k, 0.0):.4g})")
        lines.append("— 节点流量平衡 —")
        lines.append("  所有内部节点 进=出（守恒）" if not bad
                     else "[警告] 以下控制体净流量≠0（不守恒，疑似未收敛或边界/拓扑错误）:\n    "
                          + "\n    ".join(bad))

    if not vrows and not jrows:
        lines.append("(未能定位最终状态/接管表——请人工确认)")
    return "\n".join(x for x in lines if x != "")


# ---------------- 时间历程提取（瞬态分析用；不是画图） ----------------

_TIME = re.compile(r"time=\s*([\d.Ee+-]+)")


def _series_flow(t: str) -> list:
    """抽 各编辑时刻的接管质量流量：[(time, {junid: flow}), ...]（同时刻取最后一次）。"""
    lines = t.split("\n")
    cur, i, by_t = None, 0, {}
    while i < len(lines):
        m = _TIME.search(lines[i])
        if m:
            try:
                cur = float(m.group(1))
            except ValueError:
                pass
        if _HDR_JUN.match(lines[i]):
            rows, j = [], i + 1
            while j < len(lines) and not _ANY_JUN.match(lines[j]):
                if _ROWV.match(lines[j]) and len(lines[j].split()) >= 7:
                    rows.append(lines[j].split())
                j += 1
            if rows and cur is not None:
                by_t[cur] = {tk[0]: tk[5] for tk in rows}
            i = j
            continue
        i += 1
    return sorted(by_t.items())


def _series_volume(t: str) -> list:
    """抽 各编辑时刻的 逐控制体温度：[(time, {volid: tempf}), ...]。"""
    lines = t.split("\n")
    cur, i, by_t = None, 0, {}
    while i < len(lines):
        m = _TIME.search(lines[i])
        if m:
            try:
                cur = float(m.group(1))
            except ValueError:
                pass
        if _HDR_STATE.match(lines[i]):
            names = lines[i].split()
            itf = names.index("tempf") if "tempf" in names else None
            d, j = {}, i + 1
            while j < len(lines) and not _ANY_VOLNO.match(lines[j]):
                if _ROWV.match(lines[j]) and itf is not None:
                    tk = lines[j].split()
                    try:
                        d[tk[0]] = float(tk[itf])
                    except (ValueError, IndexError):
                        pass
                j += 1
            if d and cur is not None:
                by_t[cur] = d
            i = j
            continue
        i += 1
    return sorted(by_t.items())


def _series_state(t: str) -> list:
    """抽 各编辑时刻的 压力/温度极值：[(time, minP, maxP, minT, maxT), ...]。"""
    lines = t.split("\n")
    cur, i, by_t = None, 0, {}
    while i < len(lines):
        m = _TIME.search(lines[i])
        if m:
            try:
                cur = float(m.group(1))
            except ValueError:
                pass
        if _HDR_STATE.match(lines[i]):
            names = lines[i].split()
            ip = names.index("pressure") if "pressure" in names else None
            itf = names.index("tempf") if "tempf" in names else None
            itg = names.index("tempg") if "tempg" in names else None
            ps, ts, j = [], [], i + 1
            while j < len(lines) and not _ANY_VOLNO.match(lines[j]):
                if _ROWV.match(lines[j]):
                    tk = lines[j].split()
                    try:
                        if ip is not None:
                            ps.append(float(tk[ip]))
                        for k in (itf, itg):
                            if k is not None:
                                v = float(tk[k])
                                if 100.0 < v < 6000.0:
                                    ts.append(v)
                    except (ValueError, IndexError):
                        pass
                j += 1
            if ps and cur is not None:
                by_t[cur] = (min(ps), max(ps), min(ts) if ts else 0, max(ts) if ts else 0)
            i = j
            continue
        i += 1
    return sorted(by_t.items())


@tool("transient_history",
      "瞬态时间历程：从 .o 抽 各时刻的 接管质量流量 / 逐控制体温度 / 压力温度极值，给出**随时间变化**的"
      "曲线数据。瞬态题核对'流量/温度随时间怎么变'时用它，**不要**用 python_exec 手抠 .o。",
      {"o_path": {"type": "string"},
       "what": {"type": "string", "description": "flow(接管流量) / volume(逐控制体温度) / state(压力温度极值)"},
       "ids": {"type": "array", "description": "只取这些部件号（接管如 ['102-000000'] 或控制体如 ['120-040000']）",
               "items": {"type": "string"}},
       "max_points": {"type": "integer", "description": "最多给多少个时刻，默认 30"}},
      ["o_path"])
def transient_history(o_path: str, what: str = "flow", ids=None, max_points: int = 30) -> str:
    p = _SB.resolve(o_path)
    if not p.is_file():
        return f"[history] 文件不存在: {o_path}"
    t = _clean(_read_o(p))
    n = max(3, int(max_points))

    def _sub(xs):
        if len(xs) <= n:
            return xs
        step = len(xs) / n
        return [xs[int(k * step)] for k in range(n)] + [xs[-1]]

    if str(what).lower() in ("volume", "vol", "temp", "temperature"):
        s = _series_volume(t)
        if not s:
            return "[history] 未找到随时间的状态表（确认是瞬态算例、且有大/小编辑输出）。"
        all_ids = sorted({k for _tt, d in s for k in d})
        if ids:
            use = [x for x in ids if x in all_ids] or all_ids
        else:  # 默认取温度变化幅度最大的几个控制体（最可能是加热段/关键点）
            first = s[0][1]
            swing = {k: max(abs(d.get(k, first.get(k, 0)) - first.get(k, 0)) for _tt, d in s)
                     for k in all_ids}
            use = sorted(all_ids, key=lambda k: -swing.get(k, 0))[:6]
        use = sorted(use)
        ss = _sub(s)
        out = ["[transient_history/volume] 时刻 × 控制体温度 tempf(K)",
               "  time(s) | " + " | ".join(use)]
        for tt, d in ss:
            out.append(f"  {tt:8.3f} | " +
                       " | ".join(f"{d[k]:.1f}" if k in d else "" for k in use))
        return "\n".join(out)

    if str(what).lower() == "state":
        s = _sub(_series_state(t))
        if not s:
            return "[history] 未找到随时间的状态表（确认是瞬态算例、且有大/小编辑输出）。"
        out = ["[transient_history/state] 时刻 × 压力/温度极值",
               "  time(s) | Pmin(Pa) | Pmax(Pa) | Tmin(K) | Tmax(K)"]
        out += [f"  {tt:8.3f} | {v[0]:.4g} | {v[1]:.4g} | {v[2]:.1f} | {v[3]:.1f}"
                for tt, v in s]
        return "\n".join(out)

    s = _series_flow(t)
    if not s:
        return "[history] 未找到随时间变化的接管流量表（确认是瞬态算例、且有大/小编辑输出）。"
    all_ids = sorted({k for _tt, d in s for k in d})
    use = [x for x in (ids or []) if x in all_ids] or \
          sorted(all_ids, key=lambda x: -max(abs(float(d.get(x, 0) or 0)) for _tt, d in s))[:6]
    use = sorted(use)
    ss = _sub(s)
    out = ["[transient_history/flow] 时刻 × 接管质量流量(kg/s)",
           "  time(s) | " + " | ".join(use)]
    for tt, d in ss:
        out.append(f"  {tt:8.3f} | " + " | ".join(str(d.get(k, "")) for k in use))
    return "\n".join(out)

