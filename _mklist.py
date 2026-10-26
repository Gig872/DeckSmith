# -*- coding: utf-8 -*-
"""生成《_卡与题目总清单_20261026.md》：108 题抽样名单 + 全部卡资产清单。"""
import collections, io, json, os, sys
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")

SAMPLE = r"C:\relap-5\论文\_sample108.json"
TASKS = r"C:\relap-5\agent-kit\bench\tasks.jsonl"
OUT = r"C:\relap-5\论文\_卡与题目总清单_20261026.md"

picked = set(json.load(open(SAMPLE, encoding="utf-8")))
tasks = {json.loads(l)["task_id"]: json.loads(l) for l in open(TASKS, encoding="utf-8")}

FAM_CN = {
    "single_pipe_steady": "单相管流稳态", "chf_dryout": "临界热流密度", "critical_nozzle": "临界流喷嘴",
    "sbloca_blowdown": "小破口泄压", "parallel_channels": "并联通道", "lof_transient": "失流瞬态",
    "pump_loop": "泵回路", "valve_transient": "阀门瞬态", "jetmixer": "喷射混合器",
    "accumulator": "安注箱", "hs_gap": "含间隙热构件", "point_kinetics": "点堆动力学",
    "turbine": "汽轮机", "separator": "汽水分离器", "mtpljun": "多接管分流",
    "numerical_grid": "网格无关性", "numerical_dt": "时间步无关性",
    "modify_model": "模型修改", "fix_deck": "缺陷卡修复",
}
rows = sorted((tasks[t] for t in picked if t in tasks), key=lambda x: (x["family"], x["task_id"]))
by_fam = collections.Counter(r["family"] for r in rows)
by_tt = collections.Counter(r["task_type"] for r in rows)

L = []
w = L.append
w("# 卡与题目总清单（2026-10-26）\n")
w("用于跨模型与漂移实验：**108 题抽样名单**（第一节）与**迄今全部卡资产**（第二节）。\n")
w("- 抽样从 324 题有效题内按族分层进行，固定种子 `20261026`，单族最少 2 题。")
w("- 剔除名单固定为 5 题：`critical_nozzle_0001/0002/0008/0010`、`modify_012`（参考解自身守恒体检未过）。")
w("- 代码基线：`agent-kit` tag `paper-freeze-20261026` = `66f8716ba2a46d2e95cda7695d41782b01827b31`。\n")
w("## 一、108 题抽样名单\n")
w("| # | task_id | 族 | 中文名 | 任务型 |")
w("|---:|---|---|---|---|")
for i, r in enumerate(rows, 1):
    w("| %d | `%s` | %s | %s | %s |" % (i, r["task_id"], r["family"],
      FAM_CN.get(r["family"], ""), r["task_type"]))
w("")
w("**分族覆盖**（抽中/总数）：\n")
w("| 族 | 中文名 | 抽中 | 总数 |")
w("|---|---|---:|---:|")
tot_all = collections.Counter(t["family"] for t in tasks.values())
for f in sorted(by_fam):
    w("| %s | %s | %d | %d |" % (f, FAM_CN.get(f, ""), by_fam[f], tot_all[f]))
w("| **合计** | | **%d** | **%d** |\n" % (sum(by_fam.values()), sum(tot_all.values())))
w("任务型分布：T1 %d 题、T2 %d 题、T3 %d 题。\n" % (
    by_tt.get("T1", 0), by_tt.get("T2", 0), by_tt.get("T3", 0)))

w("## 二、全部卡资产\n")
w("| 位置 | 张数 | 性质 | 用途 |")
w("|---|---:|---|---|")
w("| `agent-kit/bench/decks_kon/` | 632 | 带样例库条件生成的产物卡 | 主实验（324 题 × 多轮）的可复查底稿 |")
w("| `agent-kit/bench/decks_koff/` | 105 | 无库条件生成的产物卡 | 无库对照臂 |")
w("| `agent-kit/bench/eval_lib/` | 499 | 评测用样例库（预置 48 + 学习/参考等） | `--knowledge on` 的检索库；运行前后哈希核对 0 增删改 |")
w("| `论文/数据/台架卡/` | 25 | 从 NUREG/IA 报告复原的台架参考卡 | 体量基准与拓扑对照；**20 张未能通过输入处理，见下** |")
w("| `论文/数据/台架试点/` | 24 | 台架试点各点的产物卡（含各轮 attempts） | 4.6 节表5 的数据来源 |")
w("| `论文/数据/03_A_带库全量.csv` | 324 | 主实验逐题结果 | 全文所有率值的分母 |")
w("| `论文/数据/02_参考解真值.csv` | 329 | 参考解关键标量 | L4 判据 |")
w("")
w("### 2.1 台架卡的已知状态\n")
w("`台架卡/_smoke.jsonl` 记录：**20 张全部 `ok=false`**，错误均为 `Unrecognizable card number N`；")
w("能通过的是两张 Marviken 精简卡（约 200 / 300 行）。原因见 `_体检结果.md`：")
w("扫描件 OCR 丢 `e`、`S/5`、`O/0` 混淆、整页 90°/180° 旋转。")
w("**因此台架卡不能作为「可运行参考卡」，只能用于体量基准与拓扑对照。**\n")
w("### 2.2 与 3.0 的关系\n")
w("3.0（`C:\decksmith3`）**不参与本论文的任何实验**：")
w("- 论文的 324 题、55 题无库、台架试点，全部在 `agent-kit`（2.x）上完成；")
w("- 3.0 的 `describe.py`（卡→逐词解说）与 `deck.plan`（大卡拆分）在本论文中从未被调用。")
w("")

open(OUT, "w", encoding="utf-8").write("\n".join(L))
print("written:", OUT, "| 题数", len(rows))
