# Changelog

本项目遵循 [语义化版本](https://semver.org/lang/zh-CN/)。格式参考 [Keep a Changelog](https://keepachangelog.com/zh-CN/1.1.0/)。

**版本号约定（`MAJOR.MINOR.PATCH`）**：**大功能**动第一位（1.x→2.x）；**正式版 / 小更新**动第二位
（1.0→1.1；2.0.x 全稳→2.1 正式版）；**开发里程碑 与 bug 修复**共用第三位（M1…M6 = 2.0.0…2.0.5；修 bug = x.y.**z**）。

## [未发布]

- 规划中：**2.0.x 全稳 → v2.1.0（2.x 正式版）**。

## [2.0.6] - 2026-09-11

### 新增（M7：自主评估 / 独立复核）
- **技能 `skills/70_verification.md`「自主评估」**：第一原则 **不与仿真自证**；复核五步
  （守恒/拓扑 → 饱和一致性 → 能量/量级 → **无关性** → 交叉）；结论只分
  **通过 / 存疑 / 未覆盖** 三档，**存疑必须明说、禁止拍胸口**；输出可信度报告模板与硬规矩。
- `postprocess/water.py`：独立物性估算——`sat_temp_K`（IAPWS-IF97 第 4 区**显式**饱和温度）、
  `cp_liquid`（查表插值）、`h_fg`（Watson 关联），并标注适用范围。
- 工具 **`verify_result(o, power?, mdot?, tin?)`**：
  ① **饱和一致性**（两相必在 `T_sat(p)`；单相液不得过热；单相汽不得过冷）；
  ② **能量平衡量级核对**（`ΔT ≈ Q/(ṁ·cp)`）；返回 通过/存疑/未覆盖 清单。
- 界面 **结果表顶部自动附「自主评估」结论**（`_refresh_res` 先跑 `verify_result`）。
- `20_workflow` 第 8 步改为「物理校验 + 自主评估」，工具速查补 `verify_result`。

### 测试
- `tests/test_water.py`（饱和温度对 1atm/1MPa/10MPa、超范围、单调；cp；潜热）。
- `tests/test_verify.py`（过冷液通过 / 两相一致通过 / 两相不一致存疑 / 液过热存疑 /
  汽过热通过 / 能量平衡好与坏 / 缺文件）。
- 实测样例：对物理自洽的两相例**通过**；对人为造的两相不一致例**如实报存疑**。

## [2.0.5] - 2026-09-11

### 新增（M6：agent 用图讲结果）
- **技能 `skills/60_plotting.md`「用图讲结果（读图解读）」**：铁律**先拿数再讲图**；
  读图三步（定坐标→抓特征→挂物理）；**特征→判据对照表**（voidg→1 烧干 / 流量平台 壅塞 /
  流量衰减·反转 LOF / 压力单调降+空泡升 LOCA / 末端平台 稳态 / 振荡 不稳定）；结论先行的讲法；
  以及与 `check_sanity` 体检一致、异常工况必须点名等边界。
- `postprocess/features.py`：`curve_features`（趋势 / 峰·谷(值@时刻) / 末端平台 / 阈值穿越 / 振荡，
  纯函数可测）+ `format_features`。
- 工具 **`curve_features`**（只取特征）与 **`plot_series`**（**出图 + 特征**：装了 matplotlib 另存 PNG，
  否则零依赖 Canvas，不影响解读）。
- 界面：agent 调 `plot_series` / `curve_features` 时**自动弹出「结果图」窗口**（可预选变量）；
  「视图 ▾」加开关 **「agent 出图时自动开窗」**；同一 `(o,var)` 去重。

### 变更（试用反馈）
- **绘图支持多选任意组合**：结果图 / 批量扫描图窗口的**变量与部件都改为多选列表**，
  每个 `(变量 × 部件)` 组合各画一条线；新增 **「归一化(0–1)」** 便于同图比较不同量纲。
- **界面中文化**：变量名显示为 **`voidg（空泡份额）`** 之类（`ui/constants.VAR_LABELS`）。
- **自动出图更可靠**：新窗口 `lift + topmost + focus`（避免被主窗盖住看着像"没弹出"）；
  本轮结束时按工具轨迹**兜底补弹**（防止实时事件漏发）；聊天区提示"已弹出结果图窗口"。

### 修复
- matplotlib 出图**中文变方块**：`render_png` 设置中文字体（`Microsoft YaHei`/`SimHei`…）+
  `axes.unicode_minus=False`。
- 出图"结束时没自动弹出"：加**弹到最前**与**结束兜底**双保险（见上）。

### 测试
- `tests/test_postprocess_features.py`（升/降/平稳/振荡/平台/阈值穿越/多部件排序/格式化）。

## [2.0.4] - 2026-09-11

### 新增（M5：可选 matplotlib 后端）
- `plotenv.py`：**探库 →（征询后）自动 pip 安装 → 失败优雅降级**。
  `available` / `can_install`（打包版不可 pip，给出改用带库构建的提示）/ `install`（实时回显）/
  `ensure`（缺则征询 confirm 再装）。
- 结果图 / 批量扫描图窗口各加 **「启用 matplotlib」** 与 **「导出图片（PNG）」**；未启用时
  PNG 不导出但 Canvas 显示不受影响（降级），并给出提示。
- 界面 `_ensure_plot_backend`：确认弹窗 + **实时安装进度窗**（打印 pip 输出），失败提示后关闭。
- `envcheck` 增列 **绘图增强 matplotlib（可选）**（未装也给安装指引）。
- **打包开关**：`build_exe.bat mpl` → 带 matplotlib 构建（`--collect-all matplotlib/numpy`）；
  默认基础版仍零依赖。

### 测试
- `tests/test_plotenv.py`（可用性/可安装性/打包版不可装/已装则免征询/PNG 导出）。

## [2.0.3] - 2026-09-11

### 新增（M4：批量扫描趋势图）
- `postprocess/scan.py`：`read_summary` / `param_columns`（可作横轴的自变量列）/
  `scan_series`（从 `*_summary.csv` + 各工况 `.o` 抽「参数 → 结果量」，支持末值/最大值聚合）。
- 工具 **`scan_series`**：给汇总 CSV + 横轴列 + 结果变量，返回「参数值 × 部件」趋势表。
- **独立「批量扫描趋势图」窗口**（`ui/scanwin.py`，`Toplevel`，**可多开**）：选汇总/横轴/变量/聚合/部件
  → 绘制趋势线 → 导出 CSV；从 `workspace/batch/` 自动列出汇总。
- `ui/canvaschart.py`：抽出零依赖 `tk.Canvas` 折线绘制，**结果图与扫描图共用**。
- 「视图 ▾」菜单新增 **批量扫描趋势图…（参数→结果）**。

### 变更
- `plotwin.py` 复用 `canvaschart.draw_chart`（去掉重复的绘制代码）。

### 测试
- `tests/test_postprocess_scan.py` + `tests/fixtures/sample2.o`（两工况趋势：1e6/2e6 → 350/400）。

## [2.0.2] - 2026-09-11

### 新增（M3：结果图窗口，零依赖）
- **独立「结果图」窗口**（`ui/plotwin.py`，`Toplevel`，**可多开**）：选变量/部件 → 绘制 → 导出 CSV；
  零依赖用 `tk.Canvas` 画折线（坐标轴/网格/刻度/图例）。
- `postprocess/plot.py`：`chart_spec`（纯函数，出坐标范围与各条线）+ 可选 `render_png`
  （matplotlib，未装返回 None 并降级）。
- 「视图 ▾」菜单新增 **结果图窗口…**。
- 测试：`tests/test_plot_spec.py`。

## [2.0.1] - 2026-09-11

### 新增（M2：清洗 + 导出）
- `postprocess/clean.py`：去控制字符 / 压空行；`stats`/`summary_text` 概览
  （正常结束、最终时间、错误数、编辑数、控制体·接管数）。
- 工具 **`clean_output`**（清洗 `.o` 写入工作目录 `cleaned/` + 概览）与
  **`export_series`**（把某变量时间序列导出 CSV/JSON 到 `exports/`）。
- 测试：`tests/test_postproc_clean.py`（清洗/统计/导出）。

### 修复
- `clean.stats` 与 `parse` **双次去控制字符**导致行被误削（`stats` 改传原始文本）。

## [2.0.0] - 2026-09-11

### 新增（M1：后处理·解析产品化）
- 新包 `postprocess/`：`parse.py`（**表头驱动**解析 `.o`，抽控制体状态与接管流量）、
  `extract.py`（变量目录 / 时间序列 / 导出 CSV·JSON）。
- 工具 **`list_output_vars`**（看这份 `.o` 有哪些变量/部件/时刻）与 **`extract_series`**（抽时间序列）。
- 离线测试：`tests/fixtures/sample.o` + `tests/test_postprocess.py`（无需 RELAP5）。

### 变更
- `registry._KNOWN_TOOLS` 加入 `postproc`（打包兜底）。

## [1.1.0] - 2026-09-11

### 新增
- **思考 / 工作窗口**：弹窗**实时**显示模型的思考/正文与工具调用链（`▶ 调用 …` / `◀ … 返回`）。
- **思考模式**开关：开启模型思维链（更慢更贵）。
- **模型列表从接口查询**（`GET {base_url}/models`）填入下拉，可手输；不再硬编码预设。
- **环境检测**（界面「环境检测」按钮 + `envcheck.py`，12 项 ✓/✗）。
- 多会话历史、停止（协作式中断）、术语速查、结果表、导出会话/卡片；agent 提问并入对话流。
- **单元测试** `tests/`（30 用例）+ **GitHub Actions CI**（ubuntu/windows × py3.10/3.12）。
- 打包脚本 `build_exe.bat`（PyInstaller → 单文件 `DeckSmith.exe`，含图标）。

### 变更
- 顶栏重整为 **设置 │ 视图▾ │ 导出▾ │ 会话 │ 操作 │ 状态**（开关按类归位）。
- 界面拆分为 `ui/` 包（各职责 Mixin），`decksmith.py` 变薄入口。
- 教学规范：用户**反问**时先解释再回到提问；"讲解按需（问了才讲）"。

### 移除
- **字号设置**（会破坏 ttk 输入框光标，已移除）。

### 修复
- 模型栏无法切换 / 光标错位；思考窗最终答复**重复显示**。

## [1.0.0] - 2026-09-10

### 新增
- 首个正式版：地基五层（引擎 / 约束 / 知识闭环 / 交互教学 / 物理可行性）。
- 31 工具、7 技能、三档样例库（`human` / `agent` / `learned`）；手册家族检索与自举学习。
- 目标自适应预算（按目标起档、**只在有进展时放宽、硬顶封死**）+ 沙箱与熔断。
- 三道物理体检：`check_sanity` / `result_summary` / `transient_history`。
- 参数化批量仿真（先协商框架 → 问范围 → 自动扫一批 → 汇总）。
- 桌面界面（tkinter，零第三方依赖）；打包为单文件 exe。
- **7 道硬题全部真跑通过**：失流 LOF / 失水 LOCA / 失流+失水叠加 / 沸腾(含汽率) / CHF 烧干 / 临界流壅塞 / 一二次回路耦合。
