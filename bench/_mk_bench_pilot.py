# -*- coding: utf-8 -*-
"""生成台架级试点题库：仅 1 道题（LOFT L2-5 稳态基准算例）。

铁律：nl 只给物理（台架是什么 / 部件与几何·功率·压力·温度等物理条件 / 要算的工况），
     不给建模（节点化、部件号、卡片写法）。数值全部来自报告正文，未编造。
reference / expected 缺失：本试点不造参照卡，用最小合法占位并如实标注。
"""
import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))

NL = """请为 LOFT 整体试验台架建立一个**稳态**（试验初始条件）热工水力模型，并给出一张可运行的 RELAP5 输入卡。

【台架是什么】
LOFT 是一座 50 MWt 的压水堆整体效应试验台架（IET），用于模拟商用压水堆的失水事故（LOCA）与预计运行瞬态；
它按 1/60 体积比缩放自西屋型四环路商用压水堆。堆芯加热长度 1.68 m，压力容器总高约 10 m。

【主要系统与部件（物理）】
- 反应堆系统：压力容器（内含堆芯、下降段、上下腔室）。
- 一回路主冷却系统：热管段、蒸汽发生器（U 形管式，带二次侧）、冷管段、主冷却剂泵。
  本试验的一回路含"完整环路"与"破口环路"两个环路；破口环路的蒸汽发生器以模拟体代替，
  破口位于主冷却剂泵出口处，经快开卸压阀通向卸压/抑压系统。
- 稳压器：带波动管（接热管段）与喷淋管（接冷管段），并有电加热。
- 安全注入系统：蓄压箱（ACC，含氮气覆盖）、高压安注（HPIS）、低压安注（LPIS）。
- 二次侧系统：蒸汽发生器二次侧、主蒸汽管线、给水；另有空气冷却凝汽器。
- 卸压/抑压系统（blowdown suppression tank）。

【本算例要复现的工况（试验前实测的稳态初始条件）】
- 完整环路质量流量 192.4 kg/s
- 热管段压力 14.94 MPa
- 完整环路温度 589.4 K；冷管段温度 556.6 K；堆芯温升 33.1 K
- 堆芯功率 36.0 MW；最大线功率密度 40.1 kW/m
- 稳压器：液体温度 615 K，压力 14.94 MPa，液位 1.14 m
- 蒸汽发生器二次侧：饱和温度 547.1 K，压力 5.85 MPa，质量流量 19.1 kg/s，液位 3.1293 m

【要算什么】
做稳态计算，求整个系统在此工况下的稳态解（各控制体压力/温度/空泡、各接管流量随时间不再变化）。
请真跑确认能正常结束（收敛到稳态）。"""

SPEC = {
    "task_id": "loft_L25_steady_pilot_0001",
    "family": "loft_l25_steady",
    "task_type": "T1",
    "params": {"power": 36.0e6, "mdot": 192.4},
    "nl": NL,
    # —— 试点不造参照卡：reference 留空并如实标注（evaluate() 不使用该字段）——
    "reference": "",
    "_reference_note": "本试点不提供参照卡（台架级真值将来改用实验测量值）。字段置空，非编造。",
    # —— 计划比对量：仅登记"将来要与实验测量值比对"的状态量，不含任何期望数值 ——
    "key_outputs": [
        {"var": "pressure", "agg": "last:max", "tol": 0.02, "mode": "rel"},
        {"var": "tempf", "agg": "last:max", "tol": 1.5, "mode": "abs"},
        {"var": "voidg", "agg": "last:max", "tol": 0.03, "mode": "abs"},
    ],
    "_expected_note": "expected 缺失（expected.jsonl 中无此题）→ evaluate 里 exp=None → sem_ok=False（不可判语义）。本试点只判 L1/L2，符合任务设定。",
    "_source": "NUREG/IA-???? LOFT L2-5 base case（本机 refs/nureg_ia_loft_L2-5_basecase.pdf），"
               "正文 §2.1 台架描述、§2.2 试验描述、Table 1 初始条件、Appendix B 为 new stdy-st 稳态卡。",
    "_l3_note": "family=loft_l25_steady 未在 harness.L3_POLICY 登记 → sat/energy 判据默认均施加；"
                "该判据按小参数化算例标定，台架级(多部件/两相)适用性未验证，故 phys_ok 仅供参考。",
    "context_deck": "",
    "context_name": "",
}

out = os.path.join(HERE, "tasks_bench_pilot.jsonl")
with open(out, "w", encoding="utf-8") as f:
    f.write(json.dumps(SPEC, ensure_ascii=False) + "\n")
print("wrote", out)
print("nl chars:", len(NL))
print("json ok:", bool(json.loads(open(out, encoding="utf-8").readline())["task_id"]))
