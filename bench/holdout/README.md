# holdout —— 知识库物理隔离区

## 这里是什么

原本放在 `knowledge/learned`、`knowledge/reference/agent`、`knowledge/reference/human`
下的**全部样例卡（48 张）**，由 `bench/prep_rerun.py` 移入此处。

## 为什么要隔离

这些卡与 `bench/families.py` 的题库族**一一对应**（例如 `ref_medium_pump_loop.i` ↔
`pump_loop` 族、`choked_flow_two_phase_critical.i` ↔ `critical_nozzle` 族）。
而 agent 的 `find_example` / `read_example` 工具会把命中的整张卡返回给模型，
且 `skills/20_workflow.md` 指示 agent 主动检索相近样例。

**后果**：若评测时这些卡对 agent 可见，则 `R_exec / R_phys` 中「模型自己会写」与
「照抄近邻样例」两种成分无法分离 —— 即训练/测试污染。

## 处置原则

- **不删除**：这些都是真金白银跑出来的成果，删掉是浪费。
- **不靠声明**：仅在论文里声明「未使用样例库」不算数，无法证伪。
- **物理隔离**：把卡移出 agent 在运行期可达的一切路径。评测结束后由
  `bench/restore_knowledge.py` 原样还原。

## 目录

| 子目录 | 来源 | 张数 |
|---|---|---|
| `learned/` | `knowledge/learned/` | 19 |
| `reference_agent/` | `knowledge/reference/agent/` | 26 |
| `reference_human/` | `knowledge/reference/human/` | 3 |

`MANIFEST.json` 记录每张卡的来源档位与文件名，供 `restore_knowledge.py` 精确还原。

## 用法

```bash
# 评测前：隔离（可选 --archive 同时归档旧结果，避免新旧混算）
python bench/prep_rerun.py [--archive]

# 评测后：还原
python bench/restore_knowledge.py
```

## 注意

- 评测运行期，agent 的 learned 库被重定向到各 worker 的私有目录
  （`AGENT_LEARNED_DIR`），且**每题清空**，防止跨题累积污染。
- 本目录**不得**加入 `AGENT_REFERENCE_DIR` / `AGENT_LEARNED_DIR`。
