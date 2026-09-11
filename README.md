# 卡匠 DeckSmith · RELAP5 建模智能体

> 用**自然语言**把系统描述给出来，它帮你写出**能真正跑通、且物理讲得通**的 RELAP5 输入卡（`.i`），
> 并解析 `.o` 结果；对本硕新手是**导师**，对熟手是**翻译器**。
>
> 「RELAP5 输入文件 = input deck（卡组）」，本工具把自然语言**锻造成一副卡组**——故名 **DeckSmith**。

**先做合格的大语言模型助手，再做 RELAP5 建模 agent。**

**版本：v2.1.0（2.x 正式版）** —— 带后处理 + 自主评估：`.o` 解析 / 关键量提取 / 清洗导出 /
结果图 / 批量扫描趋势图 / 独立复核（里程碑 M1–M7 = v2.0.0…v2.0.6 全部落地）。

---

## ✨ 特性

- **自然语言 → 可跑通、物理自洽的输入卡**：不臆造、必真跑、必讲物理。
- **手册检索**：从你提供的输入卡手册 `.md` 中按部件（如 `branch`/`pipe`/热构件）整组检索，
  读**文字说明**后自行构建卡片（而非抄模板）。
- **三道物理体检**：`check_sanity`（质量守恒 + 压力/温度量级）、`result_summary`（末态读数 + 拓扑/节点守恒）、
  `transient_history`（瞬态时间历程）。
- **自主评估（独立复核）**：`verify_result` 用**与仿真无关**的独立估算核对——饱和一致性
  （两相是否在 `T_sat(p)`、单相液是否过热）、能量平衡（`ΔT ≈ Q/(ṁ·cp)`）；结论分
  **通过 / 存疑 / 未覆盖**，**存疑必明说**，不靠"专家经验"。
- **后处理与出图（2.0）**：`.o` 解析/抽数/清洗导出 + **结果图 / 批量扫描趋势图**（多选任意组合变量与部件）+ 读图解读。
- **三档样例库（权威降序）**：`human`（人工种子，最高权重，只读）> `agent`（已核验、冻结）> `learned`（工作成果，可写）。
- **参数化批量仿真**：先与人协商框架 → 询问参数范围 → 自动生成一批工况、真跑、汇总成表。
- **桌面界面**（tkinter，零第三方依赖）：设置（接入/提示词/字号折叠）、多会话历史、停止、
  术语速查、结果表、环境自检、导出。

---

## 🧱 架构（薄核心 + 可插拔工具 + 技能规范）

```
decksmith.py    桌面界面入口（tkinter）
run.py          命令行入口（单次 / --chat 多轮）
core.py         主循环：LLM 决策 → 调 tool → 结果回喂 → …；会话/预算
registry.py     工具注册表（@tool 装饰器）
llm.py          OpenAI 兼容客户端（零依赖，urllib）
config.py       配置（路径可移植：环境变量 → config.json → 自动探测）
safety.py       熔断（步数/时长/token/空转/同类循环）+ 目标自适应预算 + 沙箱
usage.py        token 用量与计费
envcheck.py     环境自检
tools/          工具（知识检索 / 写卡 / RELAP5 校验链 / 自主评估 / 后处理 / 批量 / 沙箱终端 / 网络 …）
postprocess/    后处理（.o 解析 / 抽时间序列 / 清洗 / 批量趋势 / 出图 / 曲线特征 / 水物性估算）
plotenv.py      绘图后端探测与自动安装（matplotlib 可选，缺则提示并降级回 Canvas）
ui/             桌面界面（按职责分 Mixin）
skills/         技能规范（宪法 / 卡格式 / 物理 / 工作流 / 教学 / 术语 / 批量 / 读图 / 自主评估）
knowledge/      样例库（human / agent / learned）
assets/         图标
docs/           ARCHIVE.md（成果归档）、ROADMAP.md（路线图）、TESTING.md（测试者指南）、TEST_PLAN_2.0.md（2.0 验收）
dev/            开发/测试脚本
```

---

## 🚀 安装与运行

### 方式一：源码运行（推荐开发者）

```bash
# 运行时**零第三方依赖**，只需 Python ≥ 3.9（含 tkinter）
python decksmith.py        # 桌面界面
python run.py "建一个水平管稳态模型"   # 命令行单次
python run.py --chat       # 命令行多轮
python envcheck.py         # 环境自检
```

### 方式二：打包成单文件 exe（Windows）

```bash
pip install pyinstaller
build_exe.bat              # 基础版（零依赖）→ dist/DeckSmith.exe
build_exe.bat mpl          # 带 matplotlib（可导出精细 PNG，体积更大）
```

打包后**目标机器无需 Python**。首次运行会在 exe 同目录生成 `config.json` 与 `workspace/`。

---

## ⚙️ 配置

在界面「⚙ 设置」里填，或直接编辑 `config.json`（见 `config.example.json`）：

| 项 | 说明 |
|---|---|
| `api_key` / `base_url` / `model` | 模型接入（默认 DeepSeek，兼容任意 OpenAI 式端点） |
| `relap5_dir` | **你的** RELAP5 安装目录（含 `relap5.exe` 与 `tpf*` 物性文件） |
| `doc_path` | 输入卡手册 `.md` 路径（用于手册检索，**需自备**） |
| `font_size` / `system_extra` | 界面字号 / 全局提示词 |
| `prices` | 计费单价（每 1M token，示例值，可改） |

也可用环境变量：`AGENT_BASE_URL`、`AGENT_API_KEY`、`AGENT_MODEL`、`RELAP5_DIR`、`RELAP5_DOC`。

---

## 📋 依赖与前提

- **本仓库代码**：纯 Python 标准库，**运行时零第三方依赖**。
- **绘图增强（可选）**：matplotlib **非必需**——默认用内置零依赖 `Canvas` 出图；想要更精细的 PNG，
  可在「结果图 / 批量扫描图」窗口点 **「启用 matplotlib」**，程序会**探测→提示→自动 pip 安装**，
  失败则优雅降级回 Canvas。打包带库版：`build_exe.bat mpl`（默认基础版仍零依赖）。
- **RELAP5**：需**自行获取并安装**（本仓库**不包含** RELAP5 程序及其物性文件）。
- **输入卡手册**：需**自备**（本仓库**不包含**手册全文）。
- **模型**：需自备 API Key 并可联网。

> 本仓库**不包含** RELAP5 程序、物性文件或任何官方手册文本——其版权归各自所有者。

---

## 🖼 界面

运行 `python decksmith.py`（或双击 `dist/DeckSmith.exe`）后：
左侧「已规范参数」实时显示已确认的需求/意图/批量框架；右侧为对话区（agent 提问并入对话流，可直接回答或反问）、
用量计费、输入卡（无注释版）、结果表；顶栏有设置、多会话、停止、术语速查、环境检测、导出。
（截图见 `docs/`）

---

## ⚠️ 已知限制

- 物理校验聚焦**通用硬伤**（守恒/量级/拓扑）；更专业的判据由模型按需自学（查手册/联网）。
- 大规模目标受**单轮 token 上限**约束，需分批。
- 桌面界面需 Windows + 有桌面环境。
- 复杂部件（透平/点堆等）的自举仍在完善中。

---

## 📄 许可证

MIT（见 `LICENSE`）。使用本工具产生的模型与结果由使用者自行负责验证。

---

## 🙏 致谢

灵感来自 RELAP5 使用者在写卡与结果解读上的真实痛点；面向核热工领域的学习与工程辅助。
