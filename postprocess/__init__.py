# -*- coding: utf-8 -*-
"""后处理层（2.0）：解析 RELAP5 输出(.o) → 变量/时间序列 → 导出/绘图。

- parse   解析：编辑时刻 + 按表头对列（控制体 / 接管）
- extract 抽取：任意变量 × 部件 → 时间序列；导出 CSV/JSON
- clean   清洗（M2）
- plot    绘图（M3/M5，matplotlib 可选）

纯标准库，无第三方依赖。
"""
