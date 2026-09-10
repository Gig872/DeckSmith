# -*- coding: utf-8 -*-
"""知识工具：手册检索 + 两个样例库。

- 参考库(reference)：人工给的**可信种子**，agent **只读**，作为基座。
- 自主学习库(learned)：**agent 自己总结/改进**的成果，自己写、自己用。
"""
from __future__ import annotations

import os
import re
from pathlib import Path

from registry import tool, bump
from config import load

_CAP = 4200        # 非家族模式：单节截断
_FAM_CAP = 16000   # 家族模式：一个部件的整组小节（如 A-7.7 全部子节）

# 查询噪声词：出现在大量章节里但不区分主题
_STOP = {
    "the", "and", "for", "with", "cards", "card", "component", "components",
    "input", "format", "minimal", "model", "data", "required", "section",
    "how", "what", "which", "type", "fields", "field",
}

_ALIAS = {
    "pipe": ["管型", "管道"], "annulus": ["环型", "环形"],
    "tmdpvol": ["时间相关控制体"], "tmdpjun": ["时间相关接管"],
    "snglvol": ["单一控制体", "单控制体"], "sngljun": ["单一接管"],
    "branch": ["分支"], "valve": ["阀"], "pump": ["泵"],
    "accum": ["安注箱"], "separatr": ["分离器"], "turbine": ["透平"],
    "mtpljun": ["多接管", "多接点"], "heat": ["热构件"], "trip": ["触发"],
    "control": ["控制"], "table": ["通用表", "总表"],
}


def _terms(q: str) -> set[str]:
    """把自然语言查询切成可匹配的词元（原来把整句当一个词，导致总是"未检索到"）。"""
    q = (q or "").strip().lower()
    t = {q} if q else set()
    for w in re.findall(r"[a-z][a-z0-9_\-]{2,}", q):      # 拉丁词，len>=3
        if w not in _STOP:
            t.add(w)
    for w in re.findall(r"[\u4e00-\u9fff]{2,}", q):        # 中文词（>=2字）
        t.add(w)
    for k, vs in _ALIAS.items():                           # 命中别名则加简称+中文别名
        if k in t or any(v in q for v in vs):
            t.add(k)
            t.update(vs)
    t.discard("")
    return t


def _family(title: str) -> str:
    """取小节编号族，如 'A-7.7.4 ...' -> '7.7'，用于把同一部件的整组小节一起返回。"""
    m = re.match(r"^A?-?(\d+\.\d+)", title.strip())
    return m.group(1) if m else ""


def _num_prefix(title: str) -> str:
    """取章节号前缀（用于"主题"归并），如 'A-8.13 ...' -> '8'、'A-7.7.4' -> '7.7'。"""
    m = re.match(r"^A?-?(\d+(?:\.\d+)?)", title.strip())
    return m.group(1) if m else ""


def _doc_path() -> Path:
    return Path(load().doc_path)


# 三档样例库（按权威降序）：human(人工基座,最高权重,只读) > agent(agent生成的可信基座,已核验冻结)
# > learned(agent 工作成果,可写)。兼容旧名 "reference" = human + agent。
_TIERS = ["human", "agent", "learned"]


def _tier_dir(tier: str) -> Path:
    s = load()
    if tier == "learned":
        p = Path(s.learned_dir)
    else:  # human / agent 都在参考库下
        p = Path(s.reference_dir) / tier
    p.mkdir(parents=True, exist_ok=True)
    return p


def _libs(lib: str) -> list[tuple[str, Path]]:
    """返回 [(tier, dir)]，按**权威降序**（human > agent > learned）。"""
    lib = str(lib or "both").lower()
    if lib in _TIERS:
        return [(lib, _tier_dir(lib))]
    if lib == "reference":                 # 兼容旧名 = human + agent
        return [("human", _tier_dir("human")), ("agent", _tier_dir("agent"))]
    return [(t, _tier_dir(t)) for t in _TIERS]   # both/其他：全部


def _writable_tier(lib: str) -> str | None:
    """可写档：learned（默认）或 agent（可信基座，需已核验）；human 不可写。
    兼容旧名 reference → 写入 agent 档。"""
    lib = str(lib or "learned").lower()
    if lib == "learned":
        return "learned"
    if lib in ("agent", "reference"):
        return "agent"
    return None


# ---------------- 手册检索 ----------------

def _sections(md: str) -> list[dict]:
    secs, cur = [], None
    for line in md.splitlines():
        if line.startswith("#"):
            if cur:
                secs.append(cur)
            lvl = len(line) - len(line.lstrip("#"))
            cur = {"title": line.lstrip("# ").strip(), "text": "", "level": lvl}
        elif cur is not None:
            cur["text"] += line + "\n"
    if cur:
        secs.append(cur)
    return secs


def _ancestor_chain(secs: list[dict], i: int) -> list[int]:
    """从 i 往上收集祖先索引链（含自身），顺序：自身 → 根。"""
    chain, j = [], i
    while j is not None:
        chain.append(j)
        lvl = secs[j]["level"]
        j = next((k for k in range(j - 1, -1, -1) if secs[k]["level"] < lvl), None)
    return chain


def _subtree(secs: list[dict], root: int) -> list[dict]:
    """取以 root 为根的连续子树（直到下一个层级 <= root 的标题）。"""
    lvl = secs[root]["level"]
    out = []
    for k in range(root, len(secs)):
        if k > root and secs[k]["level"] <= lvl:
            break
        out.append(secs[k])
    return out


def _rendered(title: str, text: str, budget: int) -> str:
    return f"## {title}\n{text[:budget]}"


@tool("lookup_doc", "检索 RELAP5 技术手册，返回最相关章节片段（会连带该部件整组小节）。",
      {"query": {"type": "string"}, "top_k": {"type": "integer"}}, ["query"])
def lookup_doc(query: str, top_k: int = 2) -> str:
    p = _doc_path()
    if not p.is_file():
        return f"[lookup_doc] 手册不存在：{p}"
    q = query.strip().lower()
    terms = _terms(q)
    secs = _sections(p.read_text(encoding="utf-8", errors="replace"))
    scored = []
    for i, s in enumerate(secs):
        tl, tx = s["title"].lower(), s["text"].lower()
        th = sum(1 for t in terms if t in tl)          # 标题命中：强信号
        bh = sum(1 for t in terms if t in tx)          # 正文命中：弱信号
        sc = 6 * th + (1 if bh else 0)
        if sc:
            scored.append((sc, i))
    # 同分优先"更浅的层级"（部件/章节级 > 变量/子卡级），避免命中 A-4 的变量表
    scored.sort(key=lambda x: (x[0], -secs[x[1]]["level"]), reverse=True)
    # 无效检索（未命中）不计入限流，避免白白烧掉配额
    if not scored:
        return "[lookup_doc] 未检索到，换个关键词（用部件英文名，如 branch/pipe/tmdpvol/heat）。"
    best_i = scored[0][1]

    # 主题 = 最佳命中往上、标题含查询词的最高祖先的编号（branch→7.7，热构件→8）。
    # 限流**按主题计、且只计成功检索**：查过某主题 3 次就提示换主题或动手，不影响查别的部件。
    root = best_i
    for j in _ancestor_chain(secs, best_i):
        tl = secs[j]["title"].lower()
        if any(t and t in tl for t in terms):
            root = j          # 链序为 自身→根，最后一次命中即最高祖先
    topic = _num_prefix(secs[root]["title"]) or _num_prefix(secs[best_i]["title"]) or "?"
    if bump(f"lookup_doc:{topic}") > 3:
        return (f"[限流] 主题 {topic} 本任务已查 3 次。请**停止查该主题**，直接动手起草，"
                "靠 run_relap5 的报错来定位修正（换别的部件主题仍可查）。")

    head = ("(以下是手册中该部件的**文字说明/说明书**——**不是现成卡结构**。请**阅读理解**它讲了"
            "哪些卡、每张卡有哪些字段、字段含义与规则，然后**自行构建**卡片；不要在手册里找可以照抄的卡。)\n"
            "提示：一次会把该部件的整组小节（含其下全部子节）一起返回，请整段通读后再动手。\n\n")
    # 家族模式：从"族根"取整棵子树（部件规范常跨多节；不同部件族的层级深度可能不同）
    group = _subtree(secs, root)
    if len(group) <= 1:       # 族根退化为单节 → 退回普通的 top_k
        group = [secs[i] for _sc, i in scored[: max(1, top_k)]]
        return head + "\n\n".join(_rendered(s["title"], s["text"], _CAP) for s in group)
    body = "\n\n".join(f"## {s['title']}\n{s['text']}" for s in group)[:_FAM_CAP]
    return head + body


# ---------------- 术语表（讲解一致性） ----------------

@tool("glossary", "查术语含义（用于向用户统一口径地讲解）。term 可给中文或英文关键词。",
      {"term": {"type": "string"}}, ["term"])
def glossary(term: str = "") -> str:
    p = Path(load().skills_dir) / "40_glossary.md"
    if not p.is_file():
        return "[glossary] 术语表不存在。"
    txt = p.read_text(encoding="utf-8", errors="replace")
    entries = []
    for line in txt.splitlines():
        line = line.strip()
        if line.startswith("- **") and "**" in line[3:]:
            entries.append(line)
    if not term:
        return "\n".join(entries) or "(术语表为空)"
    q = term.strip().lower()
    hit = [e for e in entries if q in e.lower()]
    if not hit:  # 退一步：按别名/英文简称匹配
        for k, vs in _ALIAS.items():
            if q == k or q in vs:
                hit = [e for e in entries if k in e.lower() or any(v in e for v in vs)]
                break
    return "\n".join(hit) if hit else f"(术语表未收录「{term}」，请勿臆造，改用 ask_user 问用户。"


# ---------------- 样例库读写 ----------------

def _desc(name: str, text: str) -> str:
    for l in text.splitlines():
        if l.strip().startswith("="):
            return l.strip().lstrip("= ").strip()
    return name


@tool("list_examples", "列出样例库（三档：human 人工基座 / agent 可信基座 / learned 工作成果）。",
      {"lib": {"type": "string", "description": "human/agent/learned/reference(=human+agent)/both，默认 both"}})
def list_examples(lib: str = "both") -> str:
    out = []
    for tag, d in _libs(lib):
        names = sorted(p.stem for p in d.glob("*.i"))
        out.append(f"[{tag}] " + (", ".join(names) if names else "(空)"))
    return "\n".join(out)


@tool("read_example", "读取某个样例（按权威查：human > agent > learned）。",
      {"name": {"type": "string"},
       "lib": {"type": "string", "description": "human/agent/learned/reference/both"}},
      ["name"])
def read_example(name: str, lib: str = "both") -> str:
    for tag, d in _libs(lib):
        p = d / f"{name}.i"
        if p.is_file():
            return f"[来源:{tag}]\n" + p.read_text(encoding="utf-8")
    return f"没有样例 {name}"


@tool("find_example", "按需求检索最接近的可跑样例（按权威：human > agent > learned）。",
      {"need": {"type": "string"}, "lib": {"type": "string"}}, ["need"])
def find_example(need: str, lib: str = "both") -> str:
    if bump("find_example") > 3:
        return "[限流] find_example 本任务已用 3 次，请动手起草（write_file）并用真跑验证。"
    terms = set(re.findall(r"[a-zA-Z]{2,}", need.lower())) | set(re.findall(r"[\u4e00-\u9fff]{2,}", need))
    order = {t: -i for i, t in enumerate(_TIERS)}   # human 最高 → 同分优先
    best, bs, btag = None, -1, ""
    for tag, d in _libs(lib):
        for p in d.glob("*.i"):
            t = p.read_text(encoding="utf-8")
            desc = _desc(p.stem, t).lower() + " " + p.stem.lower()
            sc = sum(1 for w in terms if w in desc)
            rank = order.get(tag, -99)              # human(-0)>agent(-1)>learned(-2)
            if sc > bs or (sc == bs and rank > order.get(btag, -99)):
                bs, best, btag = sc, (p.stem, t), tag
    if not best:
        return "(三档皆空——可用 save_example 存入 learned)"
    if bs <= 0:
        return f"(无高相关样例；最接近的是 [{btag}] {best[0]})\n{best[1]}"
    return f"[最接近样例: {btag}/{best[0]}]\n{best[1]}"


@tool("save_example",
      "存入样例。默认存 learned（工作成果）；lib=\"agent\" 存档到可信基座（仅限已核验的可跑样例）；"
      "human 为人工基座（最高权重），只读，禁止写入。",
      {"name": {"type": "string"}, "text": {"type": "string"},
       "lib": {"type": "string", "description": "learned(默认)/agent"}},
      ["name", "text"])
def save_example(name: str, text: str, lib: str = "learned") -> str:
    tier = _writable_tier(lib)
    if tier is None:
        return ("[拒绝] human 是**人工基座**（最高权重），只读，不得写入。"
                "自己的成果请存 learned（默认），已核验的可跑样例可存 agent。")
    p = _tier_dir(tier) / f"{name}.i"
    if tier == "agent" and p.exists():
        return ("[拒绝] agent 可信基座为**冻结归档**，同名文件不可覆盖（避免改坏已核验样例）。"
                "请换名，或先存 learned。")
    try:
        p.write_text(text, encoding="utf-8")
    except OSError:
        try:
            os.chmod(p, 0o666)
            p.write_text(text, encoding="utf-8")
        except OSError as e:
            return f"[写入失败] {e}"
    label = {"learned": "learned 工作成果", "agent": "agent 可信基座（冻结归档）"}[tier]
    return f"已存入 [{label}]: {name}.i"
