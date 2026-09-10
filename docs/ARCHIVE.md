# agent-kit 归档清单（ARCHIVE）

> RELAP5 智能体：自然语言 → 可跑通、物理自洽的输入卡；导师/翻译器；自主学习。
> 归档时间：2026-09-10。全部条目均经**真跑 + 物理校验**（见各库 MANIFEST）。

## 一、分层与状态

```
7  可视化 / 出图 / 后处理展示     封存
6  界面外壳（桌面窗口 decksmith.py）  ✅ 初版（本机运行，需桌面）
─────────────── 地基线 ───────────────
5  物理可行性（意图·边界自洽·守恒·量级·校验）  ✅
4  交互与教学内核（多轮会话·引导澄清·讲解）     ✅
3  知识闭环（手册检索 + 三档库 + 自举）         ✅
2  约束（熔断 / 目标自适应预算 / 沙箱）         ✅
1  引擎（循环 / 工具注册 / LLM）               ✅
```

**桌面 App（卡匠 DeckSmith）**（第 6 层）：`decksmith.py`（tkinter 窗口）+ `usage.py`（用量/计费）。
支持主流大模型接入（预设+自定义 base_url/key/model）、全局提示词、字号、多轮会话（提问并入对话流）、
多会话历史、停止、术语速查、结果表、用量两种计量、导出、整页滚动；`build_exe.bat` 打包。

## 二、工具（31）

- **交互/教学**：`ask_user` `set_user_level` `remember_requirement` `list_requirements` `set_model_intent` `set_batch_plan`
- **知识**：`lookup_doc`（手册，层级化家族检索）`glossary` `list_examples` `read_example` `find_example` `save_example`
- **写卡/文件**：`write_file` `edit_file` `read_file` `list_files`
- **RELAP5 校验链**：`validate_i` → `run_relap5` → `parse_output` → **`check_sanity`（守恒/量级）** →
  **`result_summary`（末态读数+拓扑体检）** → **`transient_history`（瞬态时间历程）**
- **批量**：`batch_sim`（参数化扫描，含 voidg_max/mj_max/烧干判据）
- **沙箱终端/网络**：`run_command` `python_exec` `web_search` `web_fetch`
- **其它**：`calc` `get_time` `remember` `recall`

## 三、技能（7）

`00_constitution`（宪法/铁律）`10_cards`（卡格式）`15_physics`（物理可行性）
`20_workflow`（工作流）`30_teaching`（导师/翻译器）`40_glossary`（术语）`50_batch`（批量）

## 四、样例库（三档，权威降序）

| 档 | 数量 | 权威 | 读写 |
|---|---|---|---|
| `human` | 3 | 最高（人工种子） | 只读 |
| `agent` | 26 | 次之（agent 生成、已核验） | 冻结（不可同名覆盖） |
| `learned` | 13 例 + 4 模板 | 工作成果 | 可写（默认） |

- 各库含 `MANIFEST.json`：逐条 sha256 + 核验状态。
- `agent` 档：手册**全部部件类型**（15 类）+ 阀 6 子类型 + 热构件(基础/间隙) + trip + control +
  通用表 + 点堆动力学，全覆盖；**26/26 复跑通过**。

## 五、硬题攻坚账（7 题，全部真跑通过 + 独立复核）

| 题 | 关键验收结论 | 样例 |
|---|---|---|
| ①-a 失流 LOF | 流量惰转 32.4→0.18 kg/s；升温 300→387.8 K | `learned/lof_transient_pump_coastdown.i` |
| ①-b 失水 LOCA | 压力 15→3.3 MPa；void 0→0.93；质量 131.8→14.2 kg | `learned/loca_sbloca_blowdown.i` |
| ①-c 失流+失水序列 | t5 泵停、t15 破口；压力 10→2.04 MPa；质量 194→34 kg | `learned/sbloca_pumptrip_lof_loca_combined.i` |
| ②-a 沸腾(含汽率) | x: −0.048→0.379；void 0.09→0.58；Q≈ṁ·Δh | `learned/boiling_channel_quality_distribution.i` |
| ②-b CHF/烧干 | 烧干起始≈1.1–1.12 MW；壁温冲到 5000 K(材料表越界) | `learned/chf_dryout_onset_1p12MW.i` |
| ②-c 临界流/壅塞 | 流量平台 17046 kg/s；临界压比≈0.89 | `learned/choked_flow_two_phase_critical.i` |
| ③ 一二次回路耦合 | 堆芯 300 kW、SG 取 294 kW；二回路 480→486.4 K | `learned/pwr_two_loop_coupled_sg.i` |

## 六、攻坚中修掉的工具缺口（"吃透问题"）

1. 缺时间历程 → 新增 **`transient_history`**（flow/volume/state）。
2. `check_sanity` 质量误差分母用"末态质量"→排空系统误报（0.4%→19.7%）→ 改用"最大质量≈初始"。
3. 入库样例说明行未以 `*` 开头→被当卡读 → `validate_i` 新增**注释行纪律检查**；修好坏样例。
4. `validate_i` 8 位卡号误报（热构件 `1CCCGXNN`）→ 放宽到 ≤8 位。
5. `batch_sim` 缺两相量 → 补 **`voidg_max` / `voidg≈1`**。
6. `batch_sim` 缺破口流量 → 补 **`mj_max`**。
7. `run_relap5` 输出名过长被截断/撞名 → 短名 + 4 位哈希 + 进程序号。
8. RELAP5 80 字符路径上限（长路径截掉 `.o`）→ 短输出名。

## 七、运行方式

- **环境自检**：`python envcheck.py`（或界面顶栏「环境检测」按钮）——列出 Python/tkinter/依赖/
  config/API Key/RELAP5/物性文件/手册/skills/样例库/工作目录 共 12 项，标 ✓/✗。
- **桌面界面（卡匠 DeckSmith）**：`python decksmith.py`（需桌面环境；⚙设置里填 key/模型→保存，右侧对话）。
- 命令行：`python run.py "需求"`（单次）/ `python run.py --chat`（多轮会话）。
- 配置：`config.json`（模型/密钥/relap5 路径；`dtokn_budget`/`max_steps` 为**硬顶**）。
- 预算：按目标复杂度起档（S/M/L/XL），**只在有进展时逐级放宽，硬顶封死**。

## 八、可移植性（分发要点）

- **零第三方依赖**：纯 Python 标准库，无需 `pip install`（打包 exe 除外，见 build_exe.bat）。
- **无写死路径**：RELAP5 目录/技术手册按 **环境变量 → `config.json` → 多候选自动探测** 解析：
  - `RELAP5_DIR`（含 relap5.exe + tpf* 的目录）、`RELAP5_DOC`（手册 .md）、
    `AGENT_BASE_URL` / `AGENT_API_KEY` / `AGENT_MODEL`（模型接入）。
- **分发前**：清空 `config.json` 的 `api_key`（别泄露）；告诉测试者填自己的 key/model、
  并把 `relap5_dir` / `doc_path` 指向**他机器上的** RELAP5 安装与手册（或设环境变量）。
- **环境自检**：`python envcheck.py` 或界面「环境检测」按钮，一次看清缺什么。

## 九、归档清理

- `workspace/` 为工作区（含 `runs/` 输出、`batch/` 扫描件）；归档时已清 `try_*.i` 等试验残留。
- `learning` 库 4 个为**参数化模板**（含 `{{占位}}`，不直接运行），非坏件。
