# bench/cases · 真实实验案例

数据源：`C:\relap-5\refs\` 下的公开报告（NUREG/IA、NUREG/CR、EG&G、B-T 等）。
用途：为"真实案例族"与"难例集"提供**有据可查的工况**，避免拍脑袋取值。

## 一、refs/ 文档清单与可用性

| 文档 | 内容 | 用途 | 状态 |
|---|---|---|---|
| `nureg_ia_0007_marviken_JIT11_CFT21.pdf` | Marviken JIT-11/CFT-21：条件表(表2-1)、喷管几何、临界流数据 | **真实族** | ✅ 已提取 |
| `nureg_ia_0186_marviken_relap5mod3.pdf` | 同上，RELAP5/MOD3.2 评估（209 页） | 参考/交叉核 | ⏳ 待细读 |
| `edwards_obrien_relap5_3d.pdf` | Edwards-O'Brien 破口泄压(标准问题1)：几何/初值/破口/节点划分 | **真实族** | ✅ 已提取 |
| `casp_standard_problems_edwards_semiscale.pdf` | CASP 标准问题(Edwards/Semiscale)说明 | 参考 | ⏳ 待细读 |
| `nureg_ia_loft_L2-5_basecase.pdf` | LOFT 大破口 L2-5（188 页，全系统） | **难例** | ⏳ 需简化 |
| `nureg_ia_0072_loft_input_dataset.pdf` | LOFT 输入数据集（逐部件数据表） | **难例**参考 | ⏳ 需简化 |
| `loft_input_data_deck_relap5.pdf` | LOFT 基础输入卡（111 页，OCR 噪声大） | 参考 | ⚠ 不能直接用 |
| `semiscale_S-UT-5_quicklook.pdf` | Semiscale 2.5% 冷段小破口（79 页） | **难例** | ⏳ 需简化 |
| `semiscale_S-UT-8_exp_ops_spec.pdf` | Semiscale 5% 破口实验规程（70 页） | **难例** | ⏳ 需简化 |
| `nureg_ia_0052_semiscale_S-FS-1.pdf` | Semiscale 蒸汽管破裂分析 | 参考/难例 | ⏳ 需简化 |

> 全系统案例（LOFT 185 体/170 接管/256 热构件；Semiscale 175 体/197 热构件）**不做网格族**，
> 按本科生尺度**简化/缩放**后作为少量难例。

## 二、已提取的真实工况（`real_cases.json`）

- **marviken_jit11 / cft21**：容器内径 5.22 m、喷管 D=0.299/0.500 m、L=1.18/1.5 m、
  初始 5.0/4.9 MPa、近饱和水（最大过冷 <3 K / 33 K）。
- **edwards_obrien_sp1**：管 L=4.096 m、D=0.073 m、初始 7.00 MPa/513.7 K、
  破口面积 = 管截面 ×0.87、开启 ~1 ms、历时 600 ms。

字段 `verified=false` 表示**数值尚待人工核对原文**；核对后方可进入正式实验。

## 三、已入库的可跑卡（`knowledge/learned/`）

| 卡 | 内容 | 实测结果 |
|---|---|---|
| `edwards_obrien_blowdown.i` | 管 20 体破口泄压 | 正常结束；质量误差 0.01%；7.0→0.27 MPa；voidg→0.96；破口流量 1.77 kg/s |
| `marviken_critical_flow.i` | 容器→喷管临界流 | 正常结束；质量误差 0.02%；壅塞流量 2339.6 kg/s；喷管出口 voidg→0.05 |

两张卡均已 `validate_i` + 真跑核验，并登记入 `knowledge/learned/MANIFEST.json`。

## 四、踩过的坑（写卡用）

1. **管道边界接管指针**：入口写 `CCC000000`、出口写 `CCC010000`（与既有工作卡一致）；
   误写末体号（如 `CCC040000`）会报 `From volume pointer ... incorrect code`。
2. 快瞬态排空时"节点净流量≈0"**不成立**（质量在流失），故 L3 拓扑体检在快瞬态下会**误报**——
   这是校验工具本身的**已知局限**，可写入论文讨论。
3. LOFT 输入卡 PDF 是扫描 OCR，**不能直接提取复用**，只能取工况参数后自行建模。

## 五、下一步

- 细读 `ia_0186` 与 `casp_*`，补齐 Marviken/Edwards 的**实测曲线数据**（用于行为比对容差）；
- 把 LOFT L2-5、Semiscale S-UT-5/8 简化为难例卡（逐张真跑核验）；
- 缺 **CHF 真实数据**（Groeneveld/Becker）与**自然循环**（ROSA/PKL/ATLAS）——需补 PDF。
