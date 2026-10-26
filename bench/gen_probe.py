# -*- coding: utf-8 -*-
"""语域探针：把题库题面改写成「半口语」「口语」两档，其余字段（参考解/参数/关键量）原样不变。

改写红线：**信息完备、解唯一**。只做三类安全变换——
  ① 单位与数字格式化（等值，如 50000.0 W → 50 kW）
  ② 术语替换（同义，如 多接管分流部件 → 三通分流器）
  ③ 删除**冗余的派生量**（如已给面积又给当量直径）
  ④ 换开头句式（不改信息）
"""
from __future__ import annotations

import json
import os
import re

HERE = os.path.dirname(os.path.abspath(__file__))

# ---- ① 数字与单位：等值重写 ----
NUM = [
    (r"50000\.0\s*W", "50 kW"), (r"100000\.0\s*W", "100 kW"),
    (r"300000\.0\s*W", "300 kW"), (r"500000\.0\s*W", "500 kW"),
    (r"1\.0e6\s*Pa", "1 MPa"), (r"3\.0e6\s*Pa", "3 MPa"),
    (r"5\.0e6\s*Pa", "5 MPa"), (r"8\.0e5\s*Pa", "0.8 MPa"),
    (r"1\.5e6\s*Pa", "1.5 MPa"), (r"1\.0e5\s*Pa", "0.1 MPa"),
    (r"1\.00\s*cm2", "1 cm²"), (r"2\.00\s*cm2", "2 cm²"),
    (r"约\s*1e-04\s*m2", "约 1e-4 m²"), (r"约\s*2e-04\s*m2", "约 2e-4 m²"),
    (r"10\.0\s*cm2", "10 cm²"),
    (r"0\.02\s*m2", "0.02 m²"), (r"0\.01\s*m2", "0.01 m²"),
    (r"0\.005\s*m2", "0.005 m²"), (r"0\.05\s*m2", "0.05 m²"),
    (r"1\.0\s*m\b", "1 m"), (r"2\.0\s*m\b", "2 m"),
    (r"5\s*m\b", "5 m"), (r"1\.18\s*m", "1.18 m"),
    (r"2\.0\s*kg/s", "2 kg/s"), (r"1\.0\s*kg/s", "1 kg/s"),
    (r"10\.0\s*kg/s", "10 kg/s"), (r"0\.2\s*kg/s", "0.2 kg/s"),
    (r"3\s*kg/s", "3 kg/s"), (r"0\.02\s*m3/s", "0.02 m³/s"),
    (r"507\.0\s*K", "507 K"), (r"500\.0\s*K", "500 K"),
    (r"300\.0\s*K", "300 K"), (r"600\.0\s*K", "600 K"),
    (r"560\.0\s*K", "560 K"),
    (r"3\.0e6\s*Pa", "3 MPa"),
]
# ② 删除冗余派生量（括号内含"约"的换算值）
DROP_PAREN = [
    r"（圆管当量直径约[^）]*）", r"（当量直径约[^）]*）",
    r"（约[^）]*）", r"\(约[^)]*\)",
]
# ③ 术语替换：（规格书式 → 半口语, 口语）
TERMS = {
    "多接管分流部件": ("三通分流器", "一进两出的接头"),
    "喷射混合器": ("喷射器", "引射器"),
    "汽水分离器": ("分离器", "把汽和水分开的那个"),
    "人造透平": ("前置透平", "假透平"),
    "点堆动力学": ("点堆", "堆芯动力学"),
    "定压边界": ("定压出口", "出口顶着定压"),
    "定压水源": ("定压水罐", "定压的水源"),
    "流通面积": ("截面积", "过流面积"),
    "进行稳态计算": ("稳着算一下", "稳态跑一下"),
    "进行稳态": ("稳着算", "稳态算"),
    "进行瞬态": ("瞬态算一下", "算个瞬态"),
    "沿轴向划分为": ("轴向上分", "顺着分成"),
    "控制体": ("控制体", "段"),
    "可运行的": ("能跑的", "跑得起来的"),
}
# ④ 开头与连接
OPENER = {
    "请建立一个": ("想建一个", "帮我弄个"),
    "并给出可运行的 RELAP5 输入卡": ("要一张能跑的 RELAP5 卡", "给张能跑的卡"),
    "要求：": ("条件是：", "情况是这样："),
    "入口给定": ("入口给", "进口这边给"),
    "出口为": ("出口取", "出口就是"),
    "管道为圆截面": ("管子是圆截面", "管子圆管"),
    "通道为圆截面": ("通道是圆截面", "通道圆管"),
    "管壁外侧沿全长均匀加热": ("管外整段均匀加热", "外面整根管子都在加热"),
    "通道外壁沿全长均匀加热": ("通道外壁整段均匀加热", "外面整根都在加热"),
}


def rewrite(s: str, level: int) -> str:
    """level 0=半口语, 1=口语, 2=口语但**保留**冗余派生量（用于拆分"语域"与"删冗余"）。

    补充档 level=2 的用途：原探针在换语域的同时还删掉了冗余派生量，
    两个因素混在一起。KEEP 档只换语域、不删冗余，于是
      ENG vs KEEP  → 纯语域效应
      KEEP vs ORAL → 纯"删冗余"效应
    """
    for pat, rep in NUM:
        s = re.sub(pat, rep, s)
    if level != 2:                       # KEEP 档保留括号内的派生量
        for pat in DROP_PAREN:
            s = re.sub(pat, "", s)
    for k, (h, o) in TERMS.items():
        s = s.replace(k, h if level == 0 else o)
    for k, (h, o) in OPENER.items():
        s = s.replace(k, h if level == 0 else o)
    s = re.sub(r"\s{2,}", " ", s).strip()
    return s


def main():
    src = [json.loads(l) for l in open(os.path.join(HERE, "tasks.jsonl"), encoding="utf-8")]
    # 每族取前 3 题（不足则全取）
    from collections import defaultdict
    by = defaultdict(list)
    for i, t in enumerate(src):
        by[t["family"]].append(i)
    sel = []
    for f, ids in by.items():
        sel += ids[:3]
    sel.sort()
    for level, name, keep_n in ((0, "half", None), (1, "oral", None), (2, "keep", 30)):
        rows = []
        pick = sel[:keep_n] if keep_n else sel
        for i in pick:
            t = dict(src[i])                       # 复制：参考解/参数/关键量原样
            t["nl_orig"] = src[i]["nl"]
            t["nl"] = rewrite(src[i]["nl"], level)
            t["register"] = name
            rows.append(t)
        p = os.path.join(HERE, f"tasks_probe_{name}.jsonl")
        with open(p, "w", encoding="utf-8") as f:
            for r in rows:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")
        print(f"{name}: {len(rows)} 题 -> {p}")


if __name__ == "__main__":
    main()
