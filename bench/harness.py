# -*- coding: utf-8 -*-
"""单题评测：智能体生成/改造/修复 → L1–L4 判定 → 记录。

由 runner.py（串行）与 _worker.py（并发）共用，避免两处判定逻辑漂移。
关键约定：
  * 任何异常都**落一条记录**（crashed=True），绝不静默丢题；
  * 超时**单列** timeout=True，不混入结构失效；
  * 首版卡单独判定 → exec_ok_first（首跑成功率）；
  * **每题清空工作目录**（防同名卡互相覆盖）；
  * 产物卡与轨迹**永久归档**，使重判始终可行。
"""
from __future__ import annotations

import json
import os
import re
import shutil
import traceback

import registry  # noqa: F401  (确保工具已注册)
import tools.relap5 as R
from bench.agg import compare, scalars
from core import Session
from llm import OutOfCredit

TRACE_DIR = None
DECK_DIR = None
KNOWLEDGE = "off"
TAG = ""

# ---- L3 逐族适用矩阵 ----
# 判据只在该族**参考解自身能通过**时才施加。
# 第一版由 bench/calib_l3_audit.py 每族抽 3 个参考解得出（3 族）；
# 第二版改为对**全部 324 个参考解**审计（bench/ref_margin.py），又发现 3 族违反，
# 故扩为 6 族。未列出的族：饱和与能量判据均适用。
L3_POLICY = {
    "accumulator":    {"sat": False, "energy": True},    # 氮气（非凝气体）：饱和关系不成立
    "chf_dryout":     {"sat": False, "energy": False},   # 强沸腾：ΔT 被 Tsat 封顶 + 能量判据不成立
    "lof_transient":  {"sat": False, "energy": False},   # 强瞬态：两条判据均不成立
    "point_kinetics": {"sat": False, "energy": False},   # 点堆动力学：无热工控制体 + 稳态假设失效
    "hs_gap":         {"sat": True,  "energy": False},   # 含间隙热构件：稳态能量式不成立
    "modify_model":   {"sat": True,  "energy": False},   # 继承瞬态算例：稳态能量式不成立
}

# 工作目录里**不清理**的项
_KEEP = {"relap5_cwd", "traces"}


def set_tag(v: str) -> None:
    global TAG
    TAG = v or ""


def set_knowledge(m: str) -> None:
    global KNOWLEDGE
    KNOWLEDGE = (m or "off").lower()


def l3_applies(family: str):
    p = L3_POLICY.get(family) or {}
    return bool(p.get("sat", True)), bool(p.get("energy", True))


def prepare(ws: str) -> None:
    """建立 trace 目录与产物卡归档目录。"""
    global TRACE_DIR, DECK_DIR
    TRACE_DIR = os.path.join(ws, "traces")
    # 标签隔离：带 tag 的批次写独立归档目录，避免覆盖主实验 decks_k*（TAG 为空时行为不变）
    _suffix = TAG or ""
    DECK_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                            f"decks_k{KNOWLEDGE}{_suffix}")
    os.makedirs(TRACE_DIR, exist_ok=True)
    os.makedirs(DECK_DIR, exist_ok=True)


def clear_workspace(s) -> None:
    """每题独立：清空工作目录里的题间产物（保留 relap5_cwd 与 traces）。
    不清理会导致**同一 worker 内后一题覆盖前一题的同名卡**，使重判失效。"""
    root = getattr(s, "workspace", "")
    if not root or not os.path.isdir(root):
        return
    try:
        for name in os.listdir(root):
            if name in _KEEP:
                continue
            p = os.path.join(root, name)
            try:
                if os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                else:
                    os.remove(p)
            except OSError:
                pass
    except OSError:
        pass


def clear_strict_empty() -> None:
    """严格空库：每题把参考库（含 agent 档）清空一次。

    自存卡写入 agent 档、也从容 agent 档读取，故同一题内"存了再取"仍成立；
    进入下一题即清空，跨题不可见。仅在 AGENT_STRICT_EMPTY 下生效。
    """
    if os.environ.get("AGENT_STRICT_EMPTY") != "1":
        return
    ref = os.environ.get("AGENT_REFERENCE_DIR")
    if not ref:
        return
    for sub in ("human", "agent"):
        d = os.path.join(ref, sub)
        shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d, exist_ok=True)


def clear_learned(s) -> None:
    """重置**评测用** learned 库：清空（防跨题累积），若配置了学习种子则重新播入。
    仅在显式设置了 AGENT_LEARNED_DIR（隔离模式）时才动手，绝不误删真实库。"""
    if not os.environ.get("AGENT_LEARNED_DIR"):
        return
    import glob
    d = s.learned_dir
    try:
        if os.path.isdir(d):
            shutil.rmtree(d, ignore_errors=True)
        os.makedirs(d, exist_ok=True)
        seed = os.environ.get("AGENT_LEARNED_SEED")
        if seed and os.path.isdir(seed):
            for f in glob.glob(os.path.join(seed, "*.i")):
                shutil.copy2(f, os.path.join(d, os.path.basename(f)))
    except Exception:  # noqa: BLE001
        pass


def first_deck_text(out):
    """从轨迹里取 agent **第一次**写出的 .i 内容。"""
    for x in (out.trace or []):
        if x.get("tool") != "write_file":
            continue
        args = x.get("args") or {}
        if str(args.get("path") or "").endswith(".i"):
            return args.get("text")
    return None


def _archive(name: str, text: str) -> str:
    if not DECK_DIR:
        return ""
    try:
        p = os.path.join(DECK_DIR, name)
        with open(p, "w", encoding="utf-8") as f:
            f.write(text)
        return p
    except Exception:  # noqa: BLE001
        return ""


def _eval_deck(deck_rel, t, rec) -> None:
    """对一张卡施加 L1–L4，写入 rec（exec_ok / timeout / phys_ok / sem_ok / scalars）。"""
    p = R._SB.resolve(deck_rel) if deck_rel else None
    if not (p and p.is_file()):
        return
    text = p.read_text(encoding="utf-8", errors="replace")
    v = R.validate_i(text)                       # L1
    rec["l1_static"] = v.splitlines()[0] if v else ""
    msg = R.run_relap5(deck_rel, timeout=600)    # L2
    if "运行超时" in msg:
        rec["timeout"] = True
        rec["n_errors"] = -1
        return
    rec["exec_ok"] = "正常结束=True" in msg
    m = re.search(r"输出=(\S+)", msg)
    if not (rec["exec_ok"] and m):
        rec["n_errors"] = -1
        # 诊断：失败时补一次 INP-CHK 预检，区分「读入失败」与「运行失败」。
        # 该结论**不参与判分**，只入 rec["precheck"] 供分析。
        try:
            rec["precheck"] = R.precheck(text)["stage"]
        except Exception:                        # noqa: BLE001
            rec["precheck"] = "error"
        return
    o = m.group(1)
    otxt = R._read_o(R._SB.resolve(o))
    rec["end_kind"] = R.end_kind(otxt)           # 诊断字段，不参与判分
    perr = R.parse_output(o)
    mm = re.search(r"错误数=(\d+)", perr)
    rec["n_errors"] = int(mm.group(1)) if mm else None

    san = R.check_sanity(o)                      # L3a 守恒/拓扑
    sanity_ok = R.sanity_passes(san)             # 统一判据，见 tools/relap5.py:sanity_passes
    rec["check_sanity"] = san.splitlines()[0] if san else ""

    sat_on, energy_on = l3_applies(t.get("family", ""))
    verify_ok = True
    try:
        from tools.verify import assess          # L3b 饱和一致性 + L3c 能量平衡
        prm = t.get("params") or {}
        va = assess(o, power=prm.get("power"), mdot=prm.get("mdot"),
                    sat=sat_on, energy=energy_on)
        rec["l3_doubt"] = va["n_doubt"]
        rec["l3_sat_doubt"] = va["n_sat_doubt"]
        rec["l3_energy_doubt"] = va["n_energy_doubt"]
        rec["l3_sat_max_k"] = va["sat_max_margin"]
        rec["l3_energy_pct"] = va["energy_rel_pct"]
        rec["l3_sat_applicable"] = sat_on
        rec["l3_energy_applicable"] = energy_on
        verify_ok = (va["n_doubt"] == 0)
    except Exception as e:                       # noqa: BLE001
        rec["l3_err"] = str(e)[:120]
    rec["phys_ok"] = bool(sanity_ok and verify_ok)

    rec["scalars"] = scalars(otxt, t.get("key_outputs") or [])
    rec["sem_ok"] = compare(rec["scalars"], rec["expected"],   # L4
                            t.get("key_outputs") or [])


def evaluate(s, t, exp, rep) -> dict:
    """跑一次并返回 rec。任何异常都落记录，不外抛。"""
    rec = {"task_id": t["task_id"], "family": t["family"], "task_type": t["task_type"],
           "repeat": rep, "knowledge": KNOWLEDGE, "tag": TAG, "produced": "", "produced_abs": "",
           "exec_ok": False, "exec_ok_first": None,
           "timeout": False, "crashed": False, "n_errors": None,
           "phys_ok": False, "sem_ok": False, "scalars": {},
           "expected": (exp or {}).get("scalars", {}),
           "iterations": None, "tokens": 0, "say": "", "stopped": ""}
    try:
        clear_workspace(s)           # ① 每题独立工作目录
        clear_learned(s)             # ② 每题重置学习库
        clear_strict_empty()         # ③ 严格空库：每题清空参考库
        if t.get("context_name") and t.get("context_deck"):
            R._SB.resolve(t["context_name"]).write_text(t["context_deck"], encoding="utf-8")
        sess = Session(s, goal=t["nl"])
        out = sess.send(t["nl"])
        deck_rel = None
        for p in reversed(sess.meta.get("artifacts") or []):
            if p.endswith(".i"):
                deck_rel = p
                break
        if not deck_rel:
            deck_rel = t.get("context_name") or ""
        rec["produced"] = deck_rel
        try:
            rec["produced_abs"] = str(R._SB.resolve(deck_rel)) if deck_rel else ""
        except Exception:  # noqa: BLE001
            rec["produced_abs"] = ""
        # ③ 产物卡永久归档（工作目录会被下一题清空）
        if deck_rel:
            try:
                src = R._SB.resolve(deck_rel)
                if src.is_file():
                    rec["deck_archived"] = _archive(t["task_id"] + ".i",
                                                    src.read_text(encoding="utf-8",
                                                                  errors="replace"))
            except Exception:  # noqa: BLE001
                pass
        rec["iterations"] = 1 + sum(1 for x in (out.trace or []) if x.get("tool") == "run_relap5")
        rec["tokens"] = (out.usage or {}).get("total_tokens", 0)
        rec["say"] = (out.say or "")[:300]
        rec["stopped"] = out.stopped or ""
        if TRACE_DIR:                            # trace 落盘（含首版卡）
            try:
                fn = f'{t["task_id"]}_r{rep}.json'
                with open(os.path.join(TRACE_DIR, fn), "w", encoding="utf-8") as f:
                    json.dump({"task_id": t["task_id"], "trace": out.trace or [],
                               "say": out.say or "", "stopped": out.stopped or ""},
                              f, ensure_ascii=False)
            except Exception:  # noqa: BLE001
                pass
        # ---- 终态卡：L1–L4 ----
        _eval_deck(deck_rel, t, rec)
        # ---- 首版卡：L1+L2（若与终态卡相同则直接继承，省一次真跑）----
        ft = first_deck_text(out)
        if ft is not None:
            try:
                _archive(t["task_id"] + "_first.i", ft)
                final_p = R._SB.resolve(deck_rel) if deck_rel else None
                same = bool(final_p and final_p.is_file() and
                            final_p.read_text(encoding="utf-8", errors="replace") == ft)
                if same:
                    rec["exec_ok_first"] = rec["exec_ok"]
                else:
                    R._SB.resolve("_first_attempt.i").write_text(ft, encoding="utf-8")
                    m1 = R.run_relap5("_first_attempt.i", timeout=600)
                    rec["exec_ok_first"] = ("正常结束=True" in m1) and ("运行超时" not in m1)
            except Exception:  # noqa: BLE001
                pass
    except OutOfCredit:
        raise                     # 欠费外传：由上层截断整批，绝不记成"任务失败"
    except Exception as e:  # noqa: BLE001
        rec["crashed"] = True
        rec["err"] = str(e)[:300]
        rec["traceback"] = traceback.format_exc()[:1200]
    return rec
