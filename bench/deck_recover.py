# -*- coding: utf-8 -*-
r"""从 NUREG/IA 报告 PDF 中还原 RELAP5 输入卡（抽取 → 清洗 → 落地 → 试跑）v2。

v1 的教训：用「所有像卡的页」会把**报告正文里的数据表**也当成卡收进来。
v2 改为 **锚定卡头**：以 `NNN new <type>` / `NNN restart <type>` 为锚，只取锚之后的
卡密集区，并在**每个锚处切分成独立卡**（报告常把稳态卡与瞬态卡并排放在不同附录）。

用法：
  python deck_recover.py --list
  python deck_recover.py [--one K] [--run]
"""
from __future__ import annotations

import argparse, collections, io, json, os, re, sys, time

ROOT = r"C:\relap-5\agent-kit"
HERE = os.path.join(ROOT, "bench")
for p in (ROOT, HERE):
    if p not in sys.path:
        sys.path.insert(0, p)

REFS = r"C:\relap-5\refs"
OUTD = r"C:\relap-5\论文\数据\台架卡"
WS = os.path.join(ROOT, "workspace_recover")
os.makedirs(OUTD, exist_ok=True)
os.makedirs(WS, exist_ok=True)
os.environ["AGENT_WORKSPACE"] = WS
os.environ.setdefault("AGENT_LEARNED_DIR", os.path.join(WS, "learned"))

TARGETS = {
    "lstf_sbcl18":   ("lstf_SB-CL-18_input_listing.pdf",       "ROSA/LSTF SB-CL-18（小破口）MOD3"),
    "bethsy_91b":    ("nureg_ia_0103_bethsy_9-1b.pdf",         "BETHSY 9.1b MOD3"),
    "pactel":        ("nureg_ia_0145_pactel.pdf",              "PACTEL MOD3"),
    "loft_l23":      ("nureg_ia_0070_loft_L2-3.pdf",           "LOFT L2-3 MOD2"),
    "loft_l25":      ("nureg_ia_loft_L2-5_basecase.pdf",       "LOFT L2-5 MOD2"),
    "loft_l91_l33":  ("nureg_ia_0114_loft_L9-1_L3-3.pdf",      "LOFT L9-1/L3-3 MOD3"),
    "lstf_sbsg06":   ("nureg_ia_0130_lstf_SB-SG-06.pdf",       "LSTF SB-SG-06 MOD3.1"),
    "loft_lp026":    ("loft_LP-02-6_input_listing.pdf",        "LOFT LP-02-6 MOD3.2"),
    "lobi_bl44":     ("nureg_ia_0153_lobi_BL-44.pdf",          "LOBI BL-44 MOD3.2"),
    "spes_spsb03":   ("nureg_ia_0154_spes_SP-SB-03.pdf",       "SPES SP-SB-03 MOD3.2"),
    "marviken":      ("nureg_ia_0007_marviken_JIT11_CFT21.pdf", "Marviken JIT-11/CFT-21 MOD2"),
    "snuf":          ("nureg_ia_0198_snuf.pdf",                "SNUF（VVER）MOD3"),
    "loft_indata":   ("loft_input_data_deck_relap5.pdf",       "LOFT 基线输入数据集"),
}

# 卡号必须是**整数**且**后接空白或行尾**——
#   既排除 `15682417.`（数值续行）、`333. 0 1`，也排除 `148: dp downc-lowpl`（报告说明行）
CARD = re.compile(r"^\s*(\d{3,8})(?=\s|$)")
# 卡头：`NNN new` / `NNN newath` / `NNN restart`（后接问题类型）
ANCHOR = re.compile(r"^\s*\d{3,8}\s+(new|newath|restart)\s+\S", re.I)
# 报告中常在卡号前印一段"分隔装饰"（如 `-____I-- 1------1- `），需裁掉
_PREFIX = re.compile(r"(?<![\dA-Za-z])(\d{3,8})\s")


def crop_card(s):
    if s.lstrip().startswith("*"):
        return s
    m = _PREFIX.search(s)
    if m and 0 < m.start() <= 48:
        return s[m.start():]
    return s
DATE = re.compile(r"^\s*\d{4}-\d{2}-\d{2}")
SNAP = re.compile(r"^(/JOB|/USER|/EOR|ATTACH|DEFINE|FILE|RFL|REDUCE|PURGE|IMPORT|"
                  r"RE\d{3}[A-Z]{2}|CLEAR|DELET)\b", re.I)
NUMTOK = re.compile(r"^[-+]?[0-9OIl]*\.?[0-9OIl]*(?:[eEdD][-+]?[0-9OIl]+)?$")
OCR = str.maketrans({"O": "0", "o": "0", "I": "1", "l": "1", "S": "5", "s": "5",
                     "G": "6", "B": "8", "Z": "2", "g": "9", "q": "9"})
WORDFIX = [("STOY-ST", "STDY-ST"), ("HITEMP", "HTTEMP"), ("RELAPS", "RELAP5")]


# RELAP5 合法"词"（关键字）——报告在卡后印说明文字但**不带 `*`**，
# 于是说明被当成数据 → 语法错。这里按"首个非关键字纯字母词"切出说明并加 `*`。
KW = set("""new newath restart run si stdy-st stdy-sth transnt
h2o d2o heavy nitrogen air helium argon
tmdpvol tmdpjun snglvol sngljun pipe annulus branch separator jetmixer
turbine eccmix vvalve valve pump mtpljun accum delete
time null gt ge lt le eq ne and or not ct
sattemp tempf tempg voidg voidf voidv voidgj voidfj rho rhofl rhoeg rhof rhog
p press mflowj mflowv mflowg velf velg vela
cntrlvar cntrlvar1 controlvar sum div mult function integral lag trip
power temp th tempv heatr htc sarea
on off l n y t f
equilv equilf dfwh2o fric blknon""".split())


def split_comment(s):
    """把「卡 + 无 `*` 的说明」切开；返回 (卡行, 说明或 None)。"""
    toks = s.split()
    if len(toks) < 3:
        return s, None
    for i in range(1, len(toks)):
        t = toks[i]
        core = t.strip('"').lower()
        if re.fullmatch(r"[A-Za-z][A-Za-z\-]*", t) and core not in KW and len(t) >= 3:
            return " ".join(toks[:i]), " ".join(toks[i:])
    return s, None


def _fix(t):
    # 形如 `20.-B`（尾字母是被 OCR 吃掉的数字）→ 尾字母按数字还原，其余不动
    m = re.fullmatch(r"([-+]?\d+(?:\.\d*)?)\.?([A-Za-z])", t)
    if m:
        u = m.group(1) + "." + m.group(2).translate(OCR)
        if re.fullmatch(r"[-+]?\d+(?:\.\d*)?\.\d+", u):
            return u
    if NUMTOK.match(t) and (re.search(r"\d", t) or "." in t or t in ("O", "I", "l")):
        u = t.translate(OCR)
        if re.fullmatch(r"[-+]?\d*\.?\d*(?:[eEdD][-+]?\d+)?", u):
            return u
    return t


def col_split(words, width):
    """判定页内分栏。

    三种情形：
      * 右栏词数很多（≥15%）→ 真·双栏，切两栏；
      * 右栏词数很少（<15%）→ 那是**页边注**（如 `D = 1.000`、`18.000/4`），**丢弃**；
      * 没有明显栏缝 → 单栏。
    """
    if len(words) < 30:
        return [(0, width)]
    xs = sorted(w[0] for w in words)
    lo, hi = 0.10 * width, 0.95 * width
    best, prev = None, None
    for x in xs:
        if prev is not None and lo < prev and x < hi and (x - prev) >= 18:
            if best is None or (x - prev) > (best[1] - best[0]):
                best = (prev, x)
        prev = x
    if not best:
        return [(0, width)]
    cut = (best[0] + best[1]) / 2.0
    a = sum(1 for w in words if w[0] < cut)
    b = len(words) - a
    if b < 0.15 * len(words):
        return [(0, cut)]                 # 右侧窄列＝页边注 → 丢弃
    if a < 0.15 * len(words):
        return [(cut, width)]             # 左侧窄列＝行号 → 丢弃
    return [(0, cut), (cut, width)]


def _group_rows(ws, tol=3.0):
    """按时序聚类归行（**不可用 round(y/tol) 分桶**——跨桶会把同一行拆开）。"""
    ws = sorted(ws, key=lambda w: (w[1], w[0]))
    rows = []
    for w in ws:
        if rows and abs(w[1] - rows[-1][0][1]) <= tol:
            rows[-1].append(w)
        else:
            rows.append([w])
    return rows


def page_lines(doc, pg, cw=6.0, gap_pt=1.8):
    page = doc[pg]
    ws = page.get_text("words")
    if not ws:
        return []
    out = []
    for (a, b) in col_split(ws, page.rect.width):
        sub = [w for w in ws if a <= w[0] < b]
        for row in _group_rows(sub):
            ws2 = sorted(row, key=lambda w: w[0])
            # **按实际字距决定空格**：相邻词有 ≥gap_pt 的水平空隙才插空格。
            # 用「按 x 折算列号」的老办法会把相邻字段粘成一个 token（大卡全栽在这）。
            line, prev_x1 = "", None
            for w in ws2:
                if prev_x1 is not None and (w[0] - prev_x1) >= gap_pt:
                    line += " "
                elif prev_x1 is not None and line and not line.endswith(" "):
                    pass
                line += w[4]
                prev_x1 = w[2]
            out.append(line.rstrip())
    return out


def extract_decks(pdf, min_cards=8):
    """锚定卡头 → 返回 [(anchor_line, [card_lines...]), ...]。"""
    import fitz
    doc = fitz.open(pdf)
    # 逐页收集
    pages = []
    for i in range(len(doc)):
        pages.append([crop_card(x) for x in page_lines(doc, i)])
    # 找锚所在页
    anchors = []
    for i, ls in enumerate(pages):
        for j, x in enumerate(ls):
            if ANCHOR.match(x):
                anchors.append((i, j))
    if not anchors:
        return []
    decks = []
    for ai, (pi, li) in enumerate(anchors):
        # 终止页：下一个锚所在页（若在同一页则用同一页）
        if ai + 1 < len(anchors):
            pend = anchors[ai + 1][0]
            lend = anchors[ai + 1][1]
        else:
            pend, lend = len(pages), None
        body = []
        for k in range(pi, pend + 1):
            if k >= len(pages):
                break
            seg = pages[k]
            if k == pi:
                seg = seg[li:]
            if k == pend and lend is not None:
                seg = seg[:lend]
            body.extend(seg)
        decks.append(body)
    # 去掉卡行太少的"锚"（误命中）
    return [d for d in decks if sum(1 for x in d if CARD.match(x)) >= min_cards]


def join_bare_cards(lines, max_absorb=14):
    """有些报告把卡的字段各占一行：裸卡号行后吸收随后的非卡号、非注释行。"""
    out, i, n = [], 0, len(lines)
    while i < n:
        s = lines[i].rstrip()
        m = CARD.match(s)
        if m and not s[m.end():].strip():
            parts = [s.strip()]
            k = i + 1
            while k < n and not CARD.match(lines[k]) and not lines[k].lstrip().startswith("*"):
                v = lines[k].strip()
                if v:
                    parts.append(v)
                k += 1
                if len(parts) > max_absorb:
                    break
            out.append(" ".join(parts))
            i = k
        else:
            out.append(s)
            i += 1
    return out


def clean(lines):
    stat = {"ocr": 0, "snap": 0, "dropped": 0}
    lines = join_bare_cards(lines)
    out = []
    for s in lines:
        s = crop_card(s.rstrip())
        if not s.strip() or DATE.match(s):
            continue
        if SNAP.match(s.strip()):
            stat["snap"] += 1
            continue
        m0 = CARD.match(s)
        if not m0 or set(m0.group(1)) == {"0"}:
            # 非卡行；**全零的"卡号"也是碎片**（真实卡号不会全零），一并丢弃
            if s.strip().startswith("*"):
                out.append(s)
            else:
                stat["dropped"] += 1
            continue
        toks = []
        for t in s.split(" "):
            if t == "":
                toks.append(t); continue
            t2 = _fix(t)
            if t2 != t:
                stat["ocr"] += 1
            toks.append(t2)
        line2 = " ".join(toks)
        for a, b in WORDFIX:
            line2 = line2.replace(a, b)
        head, note = split_comment(line2)
        out.append(head.rstrip())
        if note:
            out.append("* " + note)
    while out and out[-1].strip().startswith("*"):
        out.pop()
    if not (out and out[-1].strip() == "."):
        out.append(".")
    return out, stat


def smoke(path):
    import registry
    registry.load_plugins("tools")
    import tools.relap5 as R
    t0 = time.time()
    msg = R.run_relap5(path, timeout=900)
    return ("正常结束=True" in msg), msg.strip()[:170], round(time.time() - t0, 1)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--list", action="store_true")
    ap.add_argument("--one", default=None)
    ap.add_argument("--run", action="store_true")
    a = ap.parse_args()
    if a.list:
        for k, (f, n) in TARGETS.items():
            print("  %-14s %-40s %s" % (k, f, n))
        return
    keys = [a.one] if a.one else list(TARGETS)
    rep = []
    for k in keys:
        fn, note = TARGETS[k]
        pdf = os.path.join(REFS, fn)
        if not os.path.isfile(pdf):
            rep.append({"key": k, "err": "no pdf"}); continue
        decks = extract_decks(pdf)
        if not decks:
            rep.append({"key": k, "note": note, "decks": 0, "err": "未找到卡头(`NNN new/restart`)"})
            print(json.dumps(rep[-1], ensure_ascii=False), flush=True)
            continue
        for di, d in enumerate(decks, 1):
            cards, st = clean(d)
            name = k + ("" if di == 1 else "__d%d" % di)
            dst = os.path.join(OUTD, name + ".i")
            io.open(dst, "w", encoding="utf-8", newline="\n").write("\n".join(cards) + "\n")
            rec = {"key": name, "note": note, "cards": len(cards),
                   "ocr": st["ocr"], "snap": st["snap"], "dropped": st["dropped"]}
            if a.run:
                ok, msg, el = smoke(dst)
                rec.update({"run_ok": ok, "msg": msg, "sec": el})
            rep.append(rec)
            print(json.dumps(rec, ensure_ascii=False), flush=True)
    io.open(os.path.join(OUTD, "_recover_report.jsonl"), "w", encoding="utf-8").write(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in rep))
    print("done")


if __name__ == "__main__":
    main()
