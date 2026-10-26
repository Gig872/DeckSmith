# -*- coding: utf-8 -*-
"""任务族（family）：把"参数 → 真值卡 + 自然语言需求 + 关键标量"的生成封成函数。

设计要点（详见 PLAN.md §2）：
- **派生量随参数重算**（水力学直径、加热周长、每段功率乘子、喷管面积…），真值卡由构造自洽。
- **语义判据 = 行为等价**：只比关键标量，不比卡片文本。
"""
from __future__ import annotations

import math
from dataclasses import dataclass, field

from postprocess.water import sat_temp_K


def fmt(x: float) -> str:
    """RELAP5 定长卡可读的浮点串：不用科学计数法的 '+' 与前导零（5e+06 → 5.0e6）。"""
    import re as _re
    s = f"{float(x):.6g}"
    m = _re.fullmatch(r"(-?)([\d.]+)[eE]([+-]?)(\d+)", s)
    if m:
        sign, mant, esign, exp = m.groups()
        if "." not in mant:
            mant += ".0"
        exp = exp.lstrip("0") or "0"
        return f"{sign}{mant}e{'-' if esign == '-' else ''}{exp}"
    if "." not in s:
        s += ".0"
    return s


@dataclass
class TaskSpec:
    task_id: str
    family: str
    params: dict
    nl: str
    reference: str
    key_outputs: list = field(default_factory=list)
    task_type: str = "T1"        # T1 从零建模 / T2 改造既有模型 / T3 排错修复
    context_deck: str = ""       # T2/T3：提供给模型的输入卡
    context_name: str = ""       # T2/T3：写入工作目录的文件名


# ================= 族 1：单管受热稳态 =================
KEY_SINGLE_PIPE = [          # 只比输出量：温度/空泡/压力；流量是题面给定，不作考察
    {"var": "tempf", "agg": "last:max", "tol": 1.5, "mode": "abs"},
    {"var": "voidg", "agg": "last:max", "tol": 0.03, "mode": "abs"},
    {"var": "pressure", "agg": "last:max", "tol": 0.02, "mode": "rel"},
]


def heater_pipe(p: dict) -> tuple[str, str, list]:
    A, L, N = float(p["area"]), float(p["length"]), int(p["nvol"])
    m, Q, vert = float(p["mdot"]), float(p["power"]), bool(p["vertical"])
    D = math.sqrt(4.0 * A / math.pi)
    Lseg = L / N
    Ah = math.pi * D * Lseg
    mult = 1.0 / N
    ang, elev = (90.0, Lseg) if vert else (0.0, 0.0)
    orient = "竖直向上" if vert else "水平"

    L_ = [f"= 单管受热稳态: {orient}管 A={fmt(A)} L={fmt(L)} N={N} mdot={fmt(m)} Q={fmt(Q)}",
          "100  new  stdy-st", "102  si  si",
          "201  200.0  1.0e-6  0.01  3  100  200  500", "",   # 大容积低流量需长时到稳态
          "1010000  inb  tmdpvol",
          "1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1010200  3", "1010201  0.0  1.0e6  300.0",
          "1020000  inj  tmdpjun",
          f"1020101  101000000  110000000  {fmt(A)}",
          "1020200  1", f"1020201  0.0  {fmt(m)}  0.0  0.0",
          "1100000  pipe  pipe", f"1100001  {N}",
          f"1100101  {fmt(A)}  {N}", f"1100301  {fmt(Lseg)}  {N}",
          f"1100601  {fmt(ang)}  {N}"]
    if vert:
        L_.append(f"1100701  {fmt(elev)}  {N}")
    L_ += [f"1100801  4.5e-5  {fmt(D)}  {N}", f"1101001  0000000  {N}",
           f"1101101  0  {N - 1}", f"1101201  3  1.0e6  300.0  0  0  0  {N}",
           "1101300  1", f"1101301  {fmt(m)}  0.0  0.0  {N - 1}",
           "1200000  outj  sngljun",
           f"1200101  110010000  151000000  {fmt(A)}  0.0  0.0  0000",
           f"1200201  1  {fmt(m)}  0.0  0.0",
           "1510000  outb  tmdpvol",
           "1510101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
           "1510200  3", "1510201  0.0  1.0e6  300.0",
           f"11101000  {N}  2  1  0  0.0  0  0  {N}", "11101100  0  1",
           "11101101  1  0.005", "11101201  1  1", "11101301  1.0  1",
           "11101400  0", "11101401  300.0  1", "11101402  300.0  2"]
    for i in range(1, N + 1):
        L_.append(f"111015{i:02d}  110{i:02d}0000  0  1  0  {fmt(Ah)}  {i}")
    for i in range(1, N + 1):
        L_.append(f"111016{i:02d}  0  0  0  0  {fmt(Ah)}  {i}")
    for i in range(1, N + 1):
        L_.append(f"111017{i:02d}  1  {fmt(mult)}  0.0  0.0  {i}")
    for i in range(1, N + 1):
        L_.append(f"111018{i:02d}  {fmt(D)}  10.0  10.0  0.0  0.0  0.0  0.0  1.0  {i}")
    L_ += ["20200100  power", f"20200101  0.0  {fmt(Q)}",
           f"20200102  100.0  {fmt(Q)}", "20100100  s-steel", "."]
    deck = "\n".join(L_) + "\n"

    nl = (f"请建立一个{orient}的圆管稳态流动与传热模型，并给出可运行的 RELAP5 输入卡。要求："
          f"管道为圆截面，流通面积 {fmt(A)} m2、长度 {fmt(L)} m，沿轴向划分为 {N} 个控制体，"
          f"管壁粗糙度 4.5e-5 m（圆管当量直径约 {D:.4f} m）；"
          f"入口给定质量流量 {fmt(m)} kg/s、温度 300 K 的水，出口为 1.0 MPa 定压边界；"
          f"管壁外侧沿全长均匀加热，总功率 {fmt(Q)} W；进行稳态计算。")
    return deck, nl, KEY_SINGLE_PIPE


GEOMS_SINGLE = [
    {"area": 0.02, "length": 1.0, "nvol": 4, "vertical": False},
    {"area": 0.01, "length": 2.0, "nvol": 8, "vertical": True},
    {"area": 0.05, "length": 1.0, "nvol": 4, "vertical": False},
    {"area": 0.02, "length": 2.0, "nvol": 8, "vertical": True},
]
MDOTS = [2.0, 5.0, 10.0, 15.0, 20.0, 30.0]
POWERS = [5.0e4, 1.0e5, 2.0e5, 4.0e5]


def single_pipe_grid() -> list[dict]:
    return [{**g, "mdot": m, "power": q}
            for g in GEOMS_SINGLE for m in MDOTS for q in POWERS]


# ================= 族 2：竖直受热通道烧干/CHF =================
KEY_CHF = [                  # 流量为给定输入；考察空泡(烧干)与出口温度
    {"var": "voidg", "agg": "last:max", "tol": 0.03, "mode": "abs"},
    {"var": "tempf", "agg": "last:max", "tol": 5.0, "mode": "abs"},
]


def chf_dryout(p: dict) -> tuple[str, str, list]:
    Q, m = float(p["power"]), float(p["mdot"])
    N, A, L, D, P0, T0 = 8, 0.01, 2.0, 0.1128, 5.0e6, 500.0
    Lseg = L / N
    Ah = math.pi * D * Lseg
    mult = 1.0 / N
    L_ = [f"= 竖直受热通道烧干/CHF: 8体A=0.01 L=2m, 入口{fmt(m)}kg/s {fmt(P0)}Pa/{T0}K, 总功率{fmt(Q)}W",
          "100  new  stdy-st", "102  si  si",
          "201  50.0  1.0e-6  0.01  3  100  200  500", "",
          "1010000  inb  tmdpvol",
          "1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1010200  3", f"1010201  0.0  {fmt(P0)}  {fmt(T0)}",
          "1020000  inj  tmdpjun",
          f"1020101  101000000  110000000  {fmt(A)}",
          "1020200  1", f"1020201  0.0  {fmt(m)}  0.0  0.0",
          "1100000  pipe  pipe", f"1100001  {N}",
          f"1100101  {fmt(A)}  {N}", f"1100301  {fmt(Lseg)}  {N}",
          f"1100601  90.0  {N}", f"1100701  {fmt(Lseg)}  {N}",
          f"1100801  4.5e-5  {fmt(D)}  {N}", f"1101001  0000000  {N}",
          f"1101101  0  {N - 1}", f"1101201  3  {fmt(P0)}  {fmt(T0)}  0  0  0  {N}",
          "1101300  1", f"1101301  {fmt(m)}  0.0  0.0  {N - 1}",
          "1200000  outj  sngljun",
          f"1200101  110010000  151000000  {fmt(A)}  0.0  0.0  0000",
          f"1200201  1  {fmt(m)}  0.0  0.0",
          "1510000  outb  tmdpvol",
          "1510101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1510200  3", f"1510201  0.0  {fmt(P0)}  {fmt(T0)}",
          f"11101000  {N}  2  1  0  0.0  0  0  {N}", "11101100  0  1",
          "11101101  1  0.005", "11101201  1  1", "11101301  1.0  1",
          "11101400  0", f"11101401  {fmt(T0)}  1", f"11101402  {fmt(T0)}  2"]
    for i in range(1, N + 1):
        L_.append(f"111015{i:02d}  110{i:02d}0000  0  1  0  {fmt(Ah)}  {i}")
    for i in range(1, N + 1):
        L_.append(f"111016{i:02d}  0  0  0  0  {fmt(Ah)}  {i}")
    for i in range(1, N + 1):
        L_.append(f"111017{i:02d}  1  {fmt(mult)}  0.0  0.0  {i}")
    for i in range(1, N + 1):
        L_.append(f"111018{i:02d}  {fmt(D)}  10.0  10.0  0.0  0.0  0.0  0.0  1.0  {i}")
    L_ += ["20200100  power", f"20200101  0.0  {fmt(Q)}",
           f"20200102  100.0  {fmt(Q)}", "20100100  s-steel", "."]
    deck = "\n".join(L_) + "\n"

    nl = (f"请建立一个竖直向上的受热通道稳态模型，给出可运行的 RELAP5 输入卡。要求："
          f"通道为圆截面，流通面积 {fmt(A)} m2、长度 {fmt(L)} m，分为 {N} 个控制体，"
          f"当量直径约 {D} m、粗糙度 4.5e-5 m；入口为 {fmt(P0)} Pa、{T0} K 的水，"
          f"质量流量 {fmt(m)} kg/s；出口定压 {fmt(P0)} Pa；"
          f"通道外壁沿全长均匀加热，总功率 {fmt(Q)} W；进行稳态计算。")
    return deck, nl, KEY_CHF


CHF_POWERS = [3.0e5, 6.0e5, 9.0e5, 1.1e6]
CHF_MDOTS = [1.0, 1.5, 2.0]


def chf_grid() -> list[dict]:
    return [{"power": q, "mdot": m} for q in CHF_POWERS for m in CHF_MDOTS]


# ================= 族 3：临界流壅塞（喷管）=================
KEY_CRIT = [                 # 壅塞流量是真正的输出；容差放宽到 10%（临界流敏感）
    {"var": "mass_flow", "agg": "last:maxabs", "tol": 0.10, "mode": "rel"},
    {"var": "voidg", "agg": "last:max", "tol": 0.05, "mode": "abs"},
]


def critical_nozzle(p: dict) -> tuple[str, str, list]:
    P0 = float(p["p0"])
    sub = float(p["subcool"])          # 过冷度 K → T0 = Tsat(P0) - sub
    Dn = float(p["nozzle_D"])
    N = 4
    Ln = 1.18
    Lseg = Ln / N
    An = math.pi * Dn ** 2 / 4.0
    tsat = sat_temp_K(P0)
    T0 = tsat - sub
    L_ = [f"= 临界流壅塞(喷管): 上游{fmt(P0)}Pa/{T0:.1f}K(过冷{sub}K) 喷管D={fmt(Dn)}m",
          "100  new  stdy-st", "102  si  si",
          "201  20.0  1.0e-6  0.01  3  100  200  500", "",
          "1010000  upb  tmdpvol",
          "1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1010200  3", f"1010201  0.0  {fmt(P0)}  {fmt(T0)}",
          "1100000  plen  snglvol",
          "1100101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          f"1100200  3  {fmt(P0)}  {fmt(T0)}",
          "1020000  inl  sngljun",
          f"1020101  101000000  110000000  {fmt(An)}  0.0  0.0  0000",
          "1020201  1  0.0  0.0  0.0",
          "1200000  nzl  pipe", f"1200001  {N}",
          f"1200101  {fmt(An)}  {N}", f"1200301  {fmt(Lseg)}  {N}",
          f"1200601  0.0  {N}", f"1200801  4.5e-5  {fmt(Dn)}  {N}",
          f"1201001  0000000  {N}", f"1201101  0  {N - 1}",
          f"1201201  3  {fmt(P0)}  {fmt(T0)}  0  0  0  {N}",
          "1201300  1", f"1201301  0.0  0.0  0.0  {N - 1}",
          "1030000  nj  sngljun",
          f"1030101  110010000  120000000  {fmt(An)}  0.0  0.0  0000",
          "1030201  1  0.0  0.0  0.0",
          "1210000  brk  sngljun",
          f"1210101  120010000  131000000  {fmt(An)}  0.0  0.0  0000",
          "1210201  1  0.0  0.0  0.0",
          "1310000  amb  tmdpvol",
          "1310101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1310200  3", "1310201  0.0  1.0e5  300.0", "."]
    deck = "\n".join(L_) + "\n"
    nl = (f"请建立一个喷管临界流(壅塞)稳态模型，给出可运行的 RELAP5 输入卡。要求："
          f"上游为 {fmt(P0)} Pa、{T0:.1f} K 的水（定压水源），经一段长 {Ln} m、"
          f"内径 {fmt(Dn)} m 的圆管喷管排入 0.1 MPa 的大气；"
          f"喷管沿轴向分为 {N} 个控制体，粗糙度 4.5e-5 m；进行稳态计算，"
          f"并报告喷管的质量流量。")
    return deck, nl, KEY_CRIT


CRIT_P0 = [3.0e6, 5.0e6, 7.0e6]
CRIT_SUB = [0.0, 20.0, 50.0]
CRIT_D = [0.05, 0.113]      # 大喷管(0.299)稳态数值不稳，改用 Marviken 瞬态覆盖


def crit_grid() -> list[dict]:
    return [{"p0": p, "subcool": s, "nozzle_D": d}
            for p in CRIT_P0 for s in CRIT_SUB for d in CRIT_D]


# ================= 族 4：小破口 LOCA（SBLOCA 泄压）=================
KEY_SBLOCA = [                                  # 瞬态：比全程峰值/最低
    {"var": "pressure", "agg": "trough:min", "tol": 0.05, "mode": "rel"},
    {"var": "voidg", "agg": "peak:max", "tol": 0.05, "mode": "abs"},
    {"var": "mass_flow", "agg": "peak:maxabs", "tol": 0.08, "mode": "rel"},
]


def sbloca(p: dict) -> tuple[str, str, list]:
    Ab = float(p["break_area"])
    P0 = float(p["p0"])
    t_trip = float(p["trip_time"])
    L_ = [f"= 小破口LOCA泄压: 系统{fmt(P0)}Pa/600K, 破口{fmt(Ab)}m2, t={fmt(t_trip)}s触发",
          "100  new  transnt", "102  si  si",
          "201  30.0  1.0e-6  0.01  3  100  200  500", "",
          "1100000  sys  snglvol",
          "1100101  0.2  1.0  0.0  0.0  0.0  0.0  0.0  0.505  0000",
          f"1100200  3  {fmt(P0)}  600.0",
          "1200000  brk  valve",
          f"1200101  110010000  131000000  {fmt(Ab)}  0.0  0.0  000100",
          "1200201  1  1.0  0.0  0.0",
          "1200300  trpvlv", "1200301  401",
          "1310000  cnt  tmdpvol",
          "1310101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1310200  3", "1310201  0.0  0.1e6  300.0",
          f"401  time  0  gt  null  0  {fmt(t_trip)}  n", "."]
    deck = "\n".join(L_) + "\n"
    nl = (f"请建立一个压水堆小破口失水事故(SBLOCA)的泄压瞬态模型，给出可运行的 RELAP5 输入卡。要求："
          f"承压系统用单个控制体表示，容积 0.2 m3，初始 {P0/1e6:.0f} MPa、600 K 过冷水；"
          f"在 t={t_trip:g} s 时破口开启，等效破口面积 {Ab*1e4:.2f} cm2（约 {Ab:.0e} m2），"
          f"向 0.1 MPa、300 K 的安全壳排放；计算 30 s 的瞬态。")
    return deck, nl, KEY_SBLOCA


SBLOCA_BREAK = [1.0e-4, 2.0e-4, 5.0e-4, 1.0e-3]
SBLOCA_P0 = [10.0e6, 15.0e6]
SBLOCA_TRIP = [2.0, 5.0, 10.0]


def sbloca_grid() -> list[dict]:
    return [{"break_area": a, "p0": p, "trip_time": t}
            for a in SBLOCA_BREAK for p in SBLOCA_P0 for t in SBLOCA_TRIP]


# ================= 族 5：并联双通道（分/合流）=================
KEY_PARALLEL = [             # 压差驱动，流量分配是真输出；出口压力是边界给定，不考察
    {"var": "mass_flow", "agg": "last:maxabs", "tol": 0.05, "mode": "rel"},
    {"var": "tempf", "agg": "last:max", "tol": 1.0, "mode": "abs"},
]


def parallel(p: dict) -> tuple[str, str, list]:
    Aa, Ab_ = float(p["areaA"]), float(p["areaB"])
    Pout = float(p["p_out"])
    Da = math.sqrt(4 * Aa / math.pi)
    Db = math.sqrt(4 * Ab_ / math.pi)
    Aj = min(Aa, Ab_)
    L_ = [f"= 并联双通道: A={fmt(Aa)} B={fmt(Ab_)} 出口{fmt(Pout)}Pa",
          "100  new  stdy-st", "102  si  si",
          "201  20.0  1.0e-6  0.01  3  100  200  500", "",
          "1010000  inb  tmdpvol",
          "1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1010200  3", "1010201  0.0  1.0e6  300.0",
          "1020000  inj  sngljun",
          f"1020101  101000000  110000000  {fmt(Aj)}  0.0  0.0  0000",
          "1020201  1  10.0  0.0  0.0",
          "1100000  split  branch", "1100001  2",
          "1100101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1100200  3  1.0e6  300.0",
          f"1101101  110000000  120000000  {fmt(Aa)}  0.0  0.0  0000",
          f"1102101  110010000  130000000  {fmt(Ab_)}  0.0  0.0  0000",
          "1101201  1.0  0.0", "1102201  1.0  0.0",
          "1200000  pipeA  pipe", "1200001  4",
          f"1200101  {fmt(Aa)}  4", "1200301  5.0  4", "1200601  0.0  4",
          f"1200801  4.5e-5  {fmt(Da)}  4", "1201001  0000000  4",
          "1201101  0  3", "1201201  3  1.0e6  300.0  0  0  0  4",
          "1201300  1", "1201301  5.0  0.0  0.0  3",
          "1300000  pipeB  pipe", "1300001  4",
          f"1300101  {fmt(Ab_)}  4", "1300301  5.0  4", "1300601  0.0  4",
          f"1300801  4.5e-5  {fmt(Db)}  4", "1301001  0000000  4",
          "1301101  0  3", "1301201  3  1.0e6  300.0  0  0  0  4",
          "1301300  1", "1301301  5.0  0.0  0.0  3",
          "1400000  merge  branch", "1400001  3",
          "1400101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          f"1400200  3  {fmt(Pout)}  300.0",
          f"1401101  120010000  140000000  {fmt(Aa)}  0.0  0.0  0000",
          f"1402101  130010000  140000000  {fmt(Ab_)}  0.0  0.0  0000",
          f"1403101  140010000  151000000  {fmt(Aj)}  0.0  0.0  0000",
          "1401201  5.0  0.0", "1402201  5.0  0.0", "1403201  10.0  0.0",
          "1510000  outb  tmdpvol",
          "1510101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1510200  3", f"1510201  0.0  {fmt(Pout)}  300.0", "."]
    deck = "\n".join(L_) + "\n"
    nl = (f"请建立一个两通道并联、再合流的稳态流动模型，给出可运行的 RELAP5 输入卡。要求："
          f"入口为 1.0 MPa、300 K 的水，经分流集管分成两条并联水平圆管支路再合流；"
          f"支路 A 流通面积 {Aa*1e4:.1f} cm2（约 {fmt(Aa)} m2，当量直径 {Da:.4f} m）、"
          f"支路 B 流通面积 {Ab_*1e4:.1f} cm2（约 {fmt(Ab_)} m2，当量直径 {Db:.4f} m）；"
          f"两管各长 5 m、分 4 个控制体、粗糙度 4.5e-5 m；出口为 {Pout/1e6:.2f} MPa 定压边界；"
          f"绝热等温，计算稳态流量分配。")
    return deck, nl, KEY_PARALLEL


PAR_AREA = [0.001, 0.002]
PAR_POUT = [0.9e6, 0.95e6]


def parallel_grid() -> list[dict]:
    return [{"areaA": a, "areaB": b, "p_out": po}
            for a in PAR_AREA for b in PAR_AREA for po in PAR_POUT]


# ================= 族 6：失流瞬态（泵惰转 LOF）=================
KEY_LOF = [                                     # 瞬态：比全程峰值/最低
    {"var": "mass_flow", "agg": "peak:maxabs", "tol": 0.05, "mode": "rel"},
    {"var": "tempf", "agg": "peak:max", "tol": 5.0, "mode": "abs"},
    {"var": "pressure", "agg": "trough:min", "tol": 0.02, "mode": "rel"},
]


def lof(p: dict) -> tuple[str, str, list]:
    inertia = float(p["inertia"])
    t_trip = float(p["trip_time"])
    Q = float(p["power"])
    N, D = 4, 0.1128
    Lseg = 0.25
    Ah = math.pi * D * Lseg
    mult = 1.0 / N
    L_ = [f"= 失流瞬态LOF(泵惰转): 转动惯量{fmt(inertia)}, t={fmt(t_trip)}s切泵, 功率{fmt(Q)}W",
          "100  new  transnt", "102  si  si",
          "201  150.0  1.0e-6  0.01  3  100  200  500", "",
          "1010000  inb  tmdpvol",
          "1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1010200  3", "1010201  0.0  1.0e6  300.0",
          "1020000  inj  sngljun",
          "1020101  101000000  105000000  0.02  0.0  0.0  0000",
          "1020201  1  1.0  0.0  0.0",
          "1050000  vol  snglvol",
          "1050101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1050200  3  1.0e6  300.0",
          "1100000  pmp  pump",
          "1100101  0.02  0.5  0.01  0.0  0.0  0.0  0000",
          "1100108  105010000  0.02  0.0  0.0  0000",
          "1100109  120000000  0.02  0.0  0.0  0000",
          "1100200  3  1.0e6  300.0",
          "1100201  1  1.0  0.0  0.0", "1100202  1  1.0  0.0  0.0",
          "1100301  -1  -1  -3  -1  -1  401  0",
          f"1100302  157.08  1.0  0.02  20.0  50.0  {fmt(inertia)}  1000.0  0.0  0.0  0.0  0.0  0.0",
          "1200000  pipe  pipe", "1200001  4",
          "1200101  0.02  4", f"1200301  {fmt(Lseg)}  4", "1200601  0.0  4",
          f"1200801  4.5e-5  {fmt(D)}  4", "1201001  0000000  4",
          "1201101  0  3", "1201201  3  1.0e6  300.0  0  0  0  4",
          "1201300  1", "1201301  1.0  0.0  0.0  3",
          "1300000  outj  sngljun",
          "1300101  120010000  141000000  0.02  0.0  0.0  0000",
          "1300201  1  1.0  0.0  0.0",
          "1410000  outb  tmdpvol",
          "1410101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1410200  3", "1410201  0.0  1.0e6  300.0",
          f"11201000  {N}  2  1  0  0.0  0  0  {N}", "11201100  0  1",
          "11201101  1  0.005", "11201201  1  1", "11201301  1.0  1",
          "11201400  0", "11201401  300.0  1", "11201402  300.0  2"]
    for i in range(1, N + 1):
        L_.append(f"112015{i:02d}  120{i:02d}0000  0  1  0  {fmt(Ah)}  {i}")
    for i in range(1, N + 1):
        L_.append(f"112016{i:02d}  0  0  0  0  {fmt(Ah)}  {i}")
    for i in range(1, N + 1):
        L_.append(f"112017{i:02d}  1  {fmt(mult)}  0.0  0.0  {i}")
    for i in range(1, N + 1):
        L_.append(f"112018{i:02d}  {fmt(D)}  10.0  10.0  0.0  0.0  0.0  0.0  1.0  {i}")
    L_ += ["20200100  power", f"20200101  0.0  {fmt(Q)}",
           f"20200102  100.0  {fmt(Q)}", "20100100  s-steel",
           f"401  time  0  gt  null  0  {fmt(t_trip)}  n", "."]
    deck = "\n".join(L_) + "\n"
    nl = (f"请建立一个泵驱动受热通道的失流(LOF)瞬态模型，给出可运行的 RELAP5 输入卡。要求："
          f"回路为 1.0 MPa、300 K 的水，由一台离心泵驱动，泵额定转速 157.08 rad/s、"
          f"额定压头 20 m、转动惯量 {inertia:g}；泵后接一段受热水平圆管"
          f"（面积 0.02 m2、长 1 m、分 4 个控制体、粗糙度 4.5e-5 m），管外均匀加热 {Q/1e3:.0f} kW；"
          f"在 t={t_trip:g} s 切除泵电机力矩，之后泵惰转、流量衰减；"
          f"计算 150 s 的瞬态，报告流量衰减与出口温度上升。")
    return deck, nl, KEY_LOF


LOF_INERTIA = [0.1, 0.2, 0.5]
LOF_TRIP = [2.0, 5.0, 10.0]
LOF_POWER = [1.0e5, 2.0e5]


def lof_grid() -> list[dict]:
    return [{"inertia": i, "trip_time": t, "power": q}
            for i in LOF_INERTIA for t in LOF_TRIP for q in LOF_POWER]


# ================= 族 7：泵驱动回路（稳态）=================
def fe(x: float) -> str:
    """科学计数法写法，如 3.0e5（RELAP5 定长卡可读）。"""
    import math as _m
    x = float(x)
    if x == 0:
        return "0.0"
    e = int(_m.floor(_m.log10(abs(x))))
    m = x / (10.0 ** e)
    return f"{m:.1f}e{e}"


def pump_loop(p: dict) -> tuple[str, str, list]:
    head = float(p["head"])          # 额定压头 m
    Pb = float(p["p_bound"])         # 回路边界压力
    L_ = [f"= 泵驱动回路: 额定压头{head:g}m, 边界{fe(Pb)}Pa",
          "100  new  stdy-st", "102  si  si",
          "201  20.0  1.0e-6  0.01  3  100  200  500", "",
          "1010000  inb  tmdpvol",
          "1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1010200  3", f"1010201  0.0  {fe(Pb)}  300.0",
          "1020000  inj  sngljun",
          "1020101  101000000  105000000  0.02  0.0  0.0  0000",
          "1020201  1  1.0  0.0  0.0",
          "1050000  vol  snglvol",
          "1050101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          f"1050200  3  {fe(Pb)}  300.0",
          "1100000  pmp  pump",
          "1100101  0.02  0.5  0.01  0.0  0.0  0.0  0000",
          "1100108  105010000  0.02  0.0  0.0  0000",
          "1100109  120000000  0.02  0.0  0.0  0000",
          f"1100200  3  {fe(Pb)}  300.0",
          "1100201  1  1.0  0.0  0.0", "1100202  1  1.0  0.0  0.0",
          "1100301  -1  -1  -3  -1  -1  0  0",
          f"1100302  157.08  1.0  0.02  {fmt(head)}  50.0  1.0  1000.0  0.0  0.0  0.0  0.0  0.0",
          "1200000  pipe  pipe", "1200001  4",
          "1200101  0.02  4", "1200301  0.25  4", "1200601  0.0  4",
          "1200801  4.5e-5  0.16  4", "1201001  0000000  4",
          "1201101  0  3", f"1201201  3  {fe(Pb)}  300.0  0  0  0  4",
          "1201300  1", "1201301  1.0  0.0  0.0  3",
          "1300000  outj  sngljun",
          "1300101  120010000  141000000  0.02  0.0  0.0  0000",
          "1300201  1  1.0  0.0  0.0",
          "1410000  outb  tmdpvol",
          "1410101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1410200  3", f"1410201  0.0  {fe(Pb)}  300.0", "."]
    deck = "\n".join(L_) + "\n"
    nl = (f"请建立一个泵驱动回路的稳态模型，给出可运行的 RELAP5 输入卡。要求："
          f"回路为 {Pb/1e6:.1f} MPa、300 K 的水，由一台离心泵驱动；泵的额定转速 157.08 rad/s、"
          f"额定流量 0.02 m3/s、额定压头 {head:g} m、转动惯量 1.0；"
          f"泵后接一段水平圆管（面积 0.02 m2、长 1 m、4 个控制体、粗糙度 4.5e-5 m）；"
          f"回路两端为同压 {Pb/1e6:.1f} MPa 边界；计算稳态循环流量。")
    return deck, nl, [{"var": "mass_flow", "agg": "last:maxabs", "tol": 0.05, "mode": "rel"}]


PUMP_HEAD = [10.0, 20.0, 40.0]
PUMP_PB = [0.3e6, 0.5e6, 0.8e6]


def pump_grid() -> list[dict]:
    return [{"head": h, "p_bound": pb} for h in PUMP_HEAD for pb in PUMP_PB]


# ================= 族 8：阀件瞬态（触发阀）=================
def valve_transient(p: dict) -> tuple[str, str, list]:
    Pu, Pd = float(p["p_up"]), float(p["p_dn"])
    tt = float(p["trip_time"])
    tend = tt + 5.0            # 保证触发发生在仿真窗口内（否则真值退化）
    L_ = [f"= 触发阀瞬态: 上游{fe(Pu)} 下游{fe(Pd)} t={fmt(tt)}s开",
          "100  new  transnt", "102  si  si",
          f"201  {fmt(tend)}  1.0e-6  0.01  3  100  200  500", "",
          "1010000  inb  tmdpvol",
          "1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1010200  3", f"1010201  0.0  {fe(Pu)}  300.0",
          "1020000  inj  sngljun",
          "1020101  101000000  110000000  0.02  0.0  0.0  0000",
          "1020201  1  1.0  0.0  0.0",
          "1100000  vol  snglvol",
          "1100101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          f"1100200  3  {fe(Pu)}  300.0",
          "1200000  trp  valve",
          "1200101  110010000  131000000  0.02  0.0  0.0  000100",
          "1200201  1  1.0  0.0  0.0",
          "1200300  trpvlv", "1200301  401",
          "1310000  outb  tmdpvol",
          "1310101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1310200  3", f"1310201  0.0  {fe(Pd)}  300.0",
          f"401  time  0  gt  null  0  {fmt(tt)}  n", "."]
    deck = "\n".join(L_) + "\n"
    nl = (f"请建立一个触发阀(trigger valve)的瞬态模型，给出可运行的 RELAP5 输入卡。要求："
          f"上游为 {Pu/1e6:.1f} MPa 的定压水（300 K），经一个初始关闭的阀门排向"
          f"{Pd/1e6:.1f} MPa 的定压边界；阀门在 t={tt:g} s 触发打开，等效流通面积 0.02 m2；"
          f"计算 {tend:g} s 的瞬态，报告阀后流量。")
    return deck, nl, [{"var": "mass_flow", "agg": "peak:maxabs", "tol": 0.08, "mode": "rel"},
                      {"var": "pressure", "agg": "trough:min", "tol": 0.03, "mode": "rel"}]


VALVE_PU = [0.8e6, 1.0e6, 1.3e6]
VALVE_PD = [0.4e6, 0.9e6]
VALVE_TRIP = [2.0, 5.0, 10.0]


def valve_grid() -> list[dict]:
    return [{"p_up": u, "p_dn": d, "trip_time": t}
            for u in VALVE_PU for d in VALVE_PD for t in VALVE_TRIP]


# ================= 族 10：喷射混合器（稳态）=================
def jetmixer(p: dict) -> tuple[str, str, list]:
    Pd_, Ps, Po = float(p["p_drv"]), float(p["p_suc"]), float(p["p_out"])
    Pj = Po + 0.15e6
    L_ = [f"= 喷射混合器: 驱动{fe(Pd_)} 吸入{fe(Ps)} 排出{fe(Po)}",
          "100  new  stdy-st", "102  si  si",
          "201  10.0  1.0e-6  0.01  3  100  200  500", "",
          "1010000  drvb  tmdpvol",
          "1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1010200  3", f"1010201  0.0  {fe(Pd_)}  300.0",
          "1020000  sucb  tmdpvol",
          "1020101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1020200  3", f"1020201  0.0  {fe(Ps)}  300.0",
          "1100000  jet  jetmixer", "1100001  3",
          "1100101  0.005  0.5  0.0  0.0  0.0  0.0  0.0  0.08  00000",
          f"1100200  3  {fe(Pj)}  300.0",
          "1101101  101000000  110000000  0.005  0.0  0.0  000000",
          "1102101  102000000  110000000  0.005  0.0  0.0  000000",
          "1103101  110010000  131000000  0.005  0.0  0.0  000000",
          "1101201  1.0  0.0", "1102201  1.0  0.0", "1103201  1.0  0.0",
          "1310000  outb  tmdpvol",
          "1310101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1310200  3", f"1310201  0.0  {fe(Po)}  300.0", "."]
    deck = "\n".join(L_) + "\n"
    nl = (f"请建立一个喷射混合器(jet mixer)的稳态模型，给出可运行的 RELAP5 输入卡。要求："
          f"驱动流来自 {Pd_/1e6:.1f} MPa 的定压水源，吸入流来自 {Ps/1e6:.1f} MPa 的定压水源，"
          f"两股在喷射混合器中混合后排出至 {Po/1e6:.1f} MPa 的定压边界；"
          f"混合器流通面积 0.005 m2；计算稳态流量分配（驱动流量与吸入流量）。")
    return deck, nl, [{"var": "mass_flow", "agg": "last:maxabs", "tol": 0.08, "mode": "rel"}]


JET_PDRV = [1.0e6, 1.3e6]
JET_PSUC = [0.8e6, 0.9e6]
JET_POUT = [0.5e6, 0.7e6]


def jet_grid() -> list[dict]:
    return [{"p_drv": a, "p_suc": b, "p_out": c}
            for a in JET_PDRV for b in JET_PSUC for c in JET_POUT]


# ================= 族 11：安注箱（瞬态注入）=================
def accum(p: dict) -> tuple[str, str, list]:
    Pt, Pp = float(p["p_tank"]), float(p["p_pipe"])
    L_ = [f"= 安注箱注入: 箱{fe(Pt)} 系统{fe(Pp)}",
          "100  new  transnt", "102  si  si",
          "110  nitrogen", "115  1.0",
          "201  2.0  1.0e-6  0.01  3  100  200  500", "",
          "1000000  acc  accum",
          "1000101  1.0  2.0  2.0  0.0  -90.0  -2.0  4.5e-5  1.13  0000",
          f"1000200  {fe(Pt)}  300.0  0.0",
          "1001101  110000000  0.001  1.0  1.0  0000",
          "1002200  1.0  1.0  2.0  2.0  0.02  0  7800.0  500.0  0",
          "1100000  pipe  pipe", "1100001  3",
          "1100101  0.05  3", "1100301  0.5  3", "1100601  0.0  3",
          "1100801  4.5e-5  0.252  3", "1101001  0000000  3",
          "1101101  0  2", f"1101201  3  {fe(Pp)}  300.0  0  0  0  3",
          "1101300  1", "1101301  1.0  0.0  0.0  2",
          "1200000  outj  sngljun",
          "1200101  110010000  131000000  0.05  0.0  0.0  0000",
          "1200201  1  1.0  0.0  0.0",
          "1310000  outb  tmdpvol",
          "1310101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1310200  3", f"1310201  0.0  {fe(Pp)}  300.0", "."]
    deck = "\n".join(L_) + "\n"
    nl = (f"请建立一个安注箱(accumulator)的瞬态注入模型，给出可运行的 RELAP5 输入卡。要求："
          f"安注箱内为 {Pt/1e6:.1f} MPa、300 K 的氮气加压水，经一根波动管注入"
          f"{Pp/1e6:.1f} MPa 的低压系统（一段水平管，出口定压 {Pp/1e6:.1f} MPa）；"
          f"计算 2 s 的瞬态，报告注入量与箱内压力变化。")
    return deck, nl, [{"var": "mass_flow", "agg": "peak:maxabs", "tol": 0.10, "mode": "rel"},
                      {"var": "pressure", "agg": "trough:min", "tol": 0.05, "mode": "rel"}]


ACC_PT = [3.0e6, 4.5e6, 6.0e6]
ACC_PP = [0.1e6, 0.3e6, 0.5e6]


def accum_grid() -> list[dict]:
    return [{"p_tank": a, "p_pipe": b} for a in ACC_PT for b in ACC_PP]


# ================= 族 9：热构件间隙传导（燃料棒三层）=================
def hs_gap(p: dict) -> tuple[str, str, list]:
    Q = float(p["power"])
    Pg = float(p["gap_p"])
    m = float(p["mdot"])
    L_ = [f"= 热构件间隙传导: 燃料棒三层(燃料/氦间隙/包壳), 功率{fe(Q)}W, 间隙初压{fe(Pg)}Pa",
          "100  new  stdy-st", "102  si  si",
          "201  100.0  1.0e-6  0.01  3  100  200  500", "",
          "1010000  inb  tmdpvol",
          "1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1010200  3", "1010201  0.0  1.55e7  560.0",
          "1020000  inj  tmdpjun",
          "1020101  101000000  110000000  0.01", "1020200  1",
          f"1020201  0.0  {fmt(m)}  0.0  0.0",
          "1100000  pipe  pipe", "1100001  1",
          "1100101  0.01  1", "1100301  1.0  1", "1100601  0.0  1",
          "1100801  4.5e-5  0.1128  1", "1101001  0000000  1",
          "1101201  3  1.55e7  560.0  0  0  0  1",
          "1200000  outj  sngljun",
          "1200101  110010000  151000000  0.01  0.0  0.0  0000",
          f"1200201  1  {fmt(m)}  0.0  0.0",
          "1510000  outb  tmdpvol",
          "1510101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1510200  3", "1510201  0.0  1.55e7  560.0",
          "11101000  1  4  2  0  0.0  0  0  4",
          f"11101001  {fe(Pg)}  110010000",
          "11101011  1.0e-6  2.0e-6  0.0  0.0  1",
          "11101100  0  1",
          "11101101  1  0.004", "11101102  1  0.0041", "11101103  1  0.0047",
          "11101201  1  1", "11101202  2  2", "11101203  3  3",
          "11101301  1.0  1", "11101302  0.0  2", "11101303  0.0  3",
          "11101701  1  1.0  0.0  0.0  1",
          "11101400  0", "11101401  560.0  1", "11101402  560.0  2",
          "11101403  560.0  3", "11101404  560.0  4",
          "11101501  110010000  0  1  1  1.0  1",
          "11101601  110010000  0  1000  1  1.0  1",
          "11101801  0.1128  10.0  10.0  0.0  0.0  0.0  0.0  1.0  1",
          "11101901  0.1128  10.0  10.0  0.0  0.0  0.0  0.0  1.0  1",
          "20200100  power", f"20200101  0.0  {fe(Q)}", f"20200102  100.0  {fe(Q)}",
          "20100100  uo2", "20100200  tbl/fctn  3  1",
          "20100201  helium  1.0", "20100251  300.0  1.0e5", "20100252  3000.0  1.0e5",
          "20100300  zr", "."]
    deck = "\n".join(L_) + "\n"
    nl = (f"请建立一个燃料棒热构件的稳态传热模型（含燃料-间隙-包壳三层），给出可运行的 RELAP5 输入卡。"
          f"要求：冷却剂为 15.5 MPa、560 K 的水，以 {m:g} kg/s 定流量通过单控制体通道；"
          f"通道外耦合一根圆柱形燃料棒：径向自内向外为 燃料（半径 4.0 mm）、"
          f"氦气间隙（4.0–4.1 mm，初始间隙压力 {Pg/1e6:.1f} MPa）、包壳（4.1–4.7 mm）；"
          f"燃料内均匀裂变热源共 {Q/1e3:.0f} kW；采用间隙传导模型。计算稳态，报告冷却剂温升。")
    return deck, nl, [{"var": "tempf", "agg": "last:max", "tol": 2.0, "mode": "abs"},
                      {"var": "voidg", "agg": "last:max", "tol": 0.05, "mode": "abs"}]


HSG_POWER = [3.0e4, 5.0e4, 8.0e4]
HSG_PG = [0.5e6, 1.0e6, 2.0e6]
HSG_MDOT = [0.2, 0.3, 0.5]


def hsg_grid() -> list[dict]:
    return [{"power": q, "gap_p": g, "mdot": m}
            for q in HSG_POWER for g in HSG_PG for m in HSG_MDOT]


# ================= 族 12：点堆动力学 =================
def point_kinetics(p: dict) -> tuple[str, str, list]:
    Q = float(p["power"])          # 反应堆总功率 W
    m = float(p["mdot"])
    N = 4
    mult = 1.0 / N
    L_ = [f"= 点堆动力学驱动加热通道: 总功率{fe(Q)}W, 流量{fmt(m)}kg/s, 反应性0",
          "100  new  stdy-st", "102  si  si",
          "201  20.0  1.0e-6  0.01  3  100  200  500", "",
          "30000000  point  separabl",
          f"30000001  no-gamma  {fe(Q)}  0.0  0.0065  1.0e-4  1.0",
          "1010000  inb  tmdpvol",
          "1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1010200  3", "1010201  0.0  15.0e6  560.0",
          "1020000  inj  tmdpjun",
          "1020101  101000000  110000000  0.01", "1020200  1",
          f"1020201  0.0  {fmt(m)}  0.0  0.0",
          "1100000  pipe  pipe", f"1100001  {N}",
          f"1100101  0.01  {N}", f"1100301  {fmt(2.0/N)}  {N}", f"1100601  0.0  {N}",
          f"1100801  4.5e-5  0.1128  {N}", f"1101001  0000000  {N}",
          f"1101101  0  {N-1}", f"1101201  3  15.0e6  560.0  0  0  0  {N}",
          "1101300  1", f"1101301  {fmt(m)}  0.0  0.0  {N-1}",
          "1200000  outj  sngljun",
          "1200101  110010000  151000000  0.01  0.0  0.0  0000",
          f"1200201  1  {fmt(m)}  0.0  0.0",
          "1510000  outb  tmdpvol",
          "1510101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1510200  3", "1510201  0.0  15.0e6  560.0",
          f"11101000  {N}  2  1  0  0.0  0  0  {N}", "11101100  0  1",
          "11101101  1  0.005", "11101201  1  1", "11101301  1.0  1",
          "11101400  0", "11101401  560.0  1", "11101402  560.0  2"]
    for i in range(1, N + 1):
        L_.append(f"111015{i:02d}  110{i:02d}0000  0  1  0  0.0886  {i}")
    for i in range(1, N + 1):
        L_.append(f"111016{i:02d}  0  0  0  0  0.0886  {i}")
    for i in range(1, N + 1):
        L_.append(f"111017{i:02d}  1000  {fmt(mult)}  0.0  0.0  {i}")
    for i in range(1, N + 1):
        L_.append(f"111018{i:02d}  0.1128  10.0  10.0  0.0  0.0  0.0  0.0  1.0  {i}")
    L_ += ["20100100  s-steel", "."]
    deck = "\n".join(L_) + "\n"
    nl = (f"请建立一个由点堆动力学驱动加热通道的稳态模型，给出可运行的 RELAP5 输入卡。要求："
          f"反应堆总功率 {Q/1e6:.1f} MW（初始反应性为 0，缓发中子份额 0.0065、"
          f"中子发生时间 1e-4 s）；冷却剂为 15.0 MPa、560 K 的水，以 {m:g} kg/s 定流量"
          f"通过一段 4 控制体的圆管通道（面积 0.01 m2、总长 2 m），通道外耦合圆柱形燃料棒热构件，"
          f"热源类型为总反应堆功率。计算稳态，报告出口温度与空泡份额。")
    return deck, nl, [{"var": "tempf", "agg": "last:max", "tol": 3.0, "mode": "abs"},
                      {"var": "voidg", "agg": "last:max", "tol": 0.05, "mode": "abs"}]


PTK_POWER = [5.0e5, 1.0e6, 2.0e6]
PTK_MDOT = [3.0, 5.0, 8.0]


def ptk_grid() -> list[dict]:
    return [{"power": q, "mdot": m} for q in PTK_POWER for m in PTK_MDOT]


# ================= 族 13：透平（turbine）=================
def turbine(p: dict) -> tuple[str, str, list]:
    Pin, Pout = float(p["p_in"]), float(p["p_out"])
    eff = float(p["eff"])
    geo = "0.05  20.0  0.0  0.0  0.0  0.0  0.0  0.252  00010"
    L_ = [f"= 透平稳态: 蒸汽源{fe(Pin)}/500K -> 人造透平(h=0) -> 透平(效率{fmt(eff)}) -> {fe(Pout)}",
          "100  new  stdy-st", "102  si  si",
          "201  60.0  1.0e-6  0.01  3  100  200  500", "",
          "1010000  stmb  tmdpvol",
          "1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1010200  3", f"1010201  0.0  {fe(Pin)}  500.0",
          "1050000  art  turbine", "1050001  1",
          f"1050101  {geo}", f"1050200  3  {fe(Pin)}  500.0",
          "1051101  101000000  105000000  0.01  0.0  0.0  000020",
          "1051201  1.0  0.0",
          "1050300  157.08  1.0  0.0  1  0  0",
          "1050400  2  0.0  0.5  0.5",
          "1100000  trb  turbine", "1100001  1",
          f"1100101  {geo}", f"1100200  3  {fe(Pin)}  500.0",
          "1101101  105010000  110000000  0.01  0.0  0.0  000020",
          "1101201  1.0  0.0",
          "1100300  157.08  1.0  0.0  1  0  0",
          f"1100400  2  {fmt(eff)}  0.5  0.5",
          "1200000  outj  sngljun",
          "1200101  110010000  131000000  0.05  0.0  0.0  0000",
          "1200201  1  1.0  0.0  0.0",
          "1310000  outb  tmdpvol",
          "1310101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1310200  3", f"1310201  0.0  {fe(Pout)}  500.0",
          "20500100  shaft1  shaft  1.0  157.08  0",
          "20500101  0  1.0  0.0  turbine  110", "."]
    deck = "\n".join(L_) + "\n"
    nl = (f"请建立一个蒸汽透平的稳态模型，给出可运行的 RELAP5 输入卡。要求："
          f"蒸汽源为 {Pin/1e6:.1f} MPa、500 K；蒸汽先经过一段人造透平（等焓、效率 0）"
          f"进入主透平，主透平等熵效率 {eff:g}、反应份额 0.5、平均级半径 0.5 m，"
          f"排出至 {Pout/1e6:.1f} MPa、500 K 的定压边界；透平与一根轴（SHAFT）相连。"
          f"计算稳态，报告透平发出的功率与质量流量。")
    return deck, nl, [{"var": "mass_flow", "agg": "last:maxabs", "tol": 0.10, "mode": "rel"},
                      {"var": "tempf", "agg": "last:max", "tol": 5.0, "mode": "abs"}]


TRB_PIN = [3.0e6, 5.0e6, 7.0e6]
TRB_POUT = [0.3e6, 0.5e6]
TRB_EFF = [0.70, 0.85]


def trb_grid() -> list[dict]:
    return [{"p_in": a, "p_out": b, "eff": e}
            for a in TRB_PIN for b in TRB_POUT for e in TRB_EFF]


# ================= 族 14：蒸汽分离器（separatr）=================
def separator(p: dict) -> tuple[str, str, list]:
    Pin, Pout = float(p["p_in"]), float(p["p_out"])
    L_ = [f"= 蒸汽分离器: 入口{fe(Pin)} -> 分离器 -> 蒸汽/液体各{fe(Pout)}",
          "100  new  stdy-st", "102  si  si",
          "201  10.0  1.0e-6  0.01  3  100  200  500", "",
          "1010000  inb  tmdpvol",
          "1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1010200  3", f"1010201  0.0  {fe(Pin)}  300.0",
          "1100000  sep  separatr", "1100001  3",
          "1100101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  00010",
          f"1100200  3  {fe(Pin)}  300.0",
          f"1101101  110010000  121000000  0.02  0.0  0.0  000000  0.5",
          f"1102101  110000000  131000000  0.02  0.0  0.0  000000  0.5",
          f"1103101  101000000  110000000  0.02  0.0  0.0  000000",
          "1101201  1.0  0.0", "1102201  1.0  0.0", "1103201  1.0  0.0",
          "1210000  stmb  tmdpvol",
          "1210101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1210200  3", f"1210201  0.0  {fe(Pout)}  300.0",
          "1310000  liqb  tmdpvol",
          "1310101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1310200  3", f"1310201  0.0  {fe(Pout)}  300.0", "."]
    deck = "\n".join(L_) + "\n"
    nl = (f"请建立一个蒸汽分离器的稳态模型，给出可运行的 RELAP5 输入卡。要求："
          f"汽水混合物自 {Pin/1e6:.1f} MPa、300 K 的定压源进入分离器（3 接管部件），"
          f"分离后蒸汽出口与液体回落口各排向 {Pout/1e6:.1f} MPa 的定压边界；"
          f"分离器流通面积 0.05 m2；计算稳态，报告蒸汽出口与液体回落的质量流量。")
    return deck, nl, [{"var": "mass_flow", "agg": "last:maxabs", "tol": 0.08, "mode": "rel"}]


SEP_PIN = [1.0e6, 1.5e6]
SEP_POUT = [0.5e6, 0.7e6, 0.9e6]


def sep_grid() -> list[dict]:
    return [{"p_in": a, "p_out": b} for a in SEP_PIN for b in SEP_POUT]


# ================= 族 15：多接管部件（mtpljun 分流）=================
def mtpljun(p: dict) -> tuple[str, str, list]:
    Ps, Pk = float(p["p_src"]), float(p["p_sink"])
    m0 = 5.0
    L_ = [f"= 多接管分流: 源{fe(Ps)} -> mtpljun(1进2出) -> 两个控制体 -> 汇{fe(Pk)}",
          "100  new  stdy-st", "102  si  si",
          "201  20.0  1.0e-6  0.01  3  100  200  500", "",
          "1010000  inb  tmdpvol",
          "1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1010200  3", f"1010201  0.0  {fe(Ps)}  300.0",
          "1100000  mj  mtpljun", "1100001  2  0",
          f"1100101  101000000  120000000  0.005  5.0  5.0  0000  1.0  1.0  1.0",
          "1100102  0  0  0  1",
          f"1100201  101000000  130000000  0.005  5.0  5.0  0000  1.0  1.0  1.0",
          "1100202  0  0  0  2",
          f"1101101  {fmt(m0)}  0.0  1", f"1101201  {fmt(m0)}  0.0  2",
          "1200000  vol1  snglvol",
          "1200101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          f"1200200  3  {fe(Ps)}  300.0",
          "1300000  vol2  snglvol",
          "1300101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          f"1300200  3  {fe(Ps)}  300.0",
          "1400000  out1  sngljun",
          "1400101  120010000  151000000  0.02  1.0  1.0  0000",
          f"1400201  1  {fmt(m0)}  0.0  0.0",
          "1500000  out2  sngljun",
          "1500101  130010000  161000000  0.02  1.0  1.0  0000",
          f"1500201  1  {fmt(m0)}  0.0  0.0",
          "1510000  outb1  tmdpvol",
          "1510101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1510200  3", f"1510201  0.0  {fe(Pk)}  300.0",
          "1610000  outb2  tmdpvol",
          "1610101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000",
          "1610200  3", f"1610201  0.0  {fe(Pk)}  300.0", "."]
    deck = "\n".join(L_) + "\n"
    nl = (f"请建立一个多接管分流部件的稳态模型，给出可运行的 RELAP5 输入卡。要求："
          f"{Ps/1e6:.1f} MPa、300 K 的水自定压源经一个多接管部件（1 进 2 出）"
          f"分成两路，分别进入两个控制体，再各经出口接管排向 {Pk/1e6:.1f} MPa 的定压边界；"
          f"两条分流接管流通面积各 0.005 m2；计算稳态，报告两条支路的质量流量。")
    return deck, nl, [{"var": "mass_flow", "agg": "last:maxabs", "tol": 0.08, "mode": "rel"}]


MTJ_PS = [1.0e6, 1.5e6]
MTJ_PK = [0.3e6, 0.5e6]


def mtj_grid() -> list[dict]:
    return [{"p_src": a, "p_sink": b} for a in MTJ_PS for b in MTJ_PK]


FAMILIES = {
    "single_pipe_steady": (single_pipe_grid, heater_pipe),
    "chf_dryout": (chf_grid, chf_dryout),
    "critical_nozzle": (crit_grid, critical_nozzle),
    "sbloca_blowdown": (sbloca_grid, sbloca),
    "parallel_channels": (parallel_grid, parallel),
    "lof_transient": (lof_grid, lof),
    "pump_loop": (pump_grid, pump_loop),
    "valve_transient": (valve_grid, valve_transient),
    "jetmixer": (jet_grid, jetmixer),
    "accumulator": (accum_grid, accum),
    "hs_gap": (hsg_grid, hs_gap),
    "point_kinetics": (ptk_grid, point_kinetics),
    "turbine": (trb_grid, turbine),
    "separator": (sep_grid, separator),
    "mtpljun": (mtj_grid, mtpljun),
}

