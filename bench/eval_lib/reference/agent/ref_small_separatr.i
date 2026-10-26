= 参考例: 蒸汽分离器(separatr) 稳态
* 部件: tmdpvol(1MPa,300K) -> separatr(3接管) -> 蒸汽出口/液体回落
* 工况: 稳态 stdy-st
* 物理: 分离器是特殊分支部件, 3个节点: N=1蒸汽出口, N=2液体回落, N=3分离器入口
*       入口972.75kg/s 等分为蒸汽出口486.37 + 液体回落486.37 (两出口边界同压0.9MPa)
* 关键坑1: 分离器接管号必须为3
* 关键坑2: 蒸汽出口(N=1)与液体回落(N=2)的"来向"都必须指分离器自身控制体:
*          N=1 from=分离器出口侧CCC010000, N=2 from=分离器入口侧CCC000000
*          (即两者都是流出分离器控制体; 若把N=2写成外部->分离器会报
*           "From connection for the vapor outlet junction or the liquid return junction is not the component volume")
* 关键坑3: 分离器控制体标识: p=0,v=0,b=0,f=1(壁面摩擦不算),e=0 -> 00010
* 关键坑4: 接管标志 fvcahs: 分离器不用水平分层(v=0), CCFL断开(f=0)
* 关键坑5: 接管卡 CCCN101 第7字码为分离器空泡份额限制(蒸汽出口VOVER/液体回落VUNDER)
* 已验证: 正常结束, 质量误差~1.7e-4 kg, 节点进=出
100  new  stdy-st
102  si  si
201  10.0  1.0e-6  0.01  3  100  200  500

1010000  inb  tmdpvol
1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1010200  3
1010201  0.0  1.0e6  300.0

1100000  sep  separatr
1100001  3
1100101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  00010
1100200  3  1.0e6  300.0
* N=1 steam outlet: from separator outlet side -> top boundary
1101101  110010000  121000000  0.02  0.0  0.0  000000  0.5
* N=2 liquid return: from separator inlet side -> bottom boundary
1102101  110000000  131000000  0.02  0.0  0.0  000000  0.5
* N=3 separator inlet: from upstream boundary -> separator inlet side
1103101  101000000  110000000  0.02  0.0  0.0  000000
1101201  1.0  0.0
1102201  1.0  0.0
1103201  1.0  0.0

1210000  stmb  tmdpvol
1210101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1210200  3
1210201  0.0  0.9e6  300.0

1310000  liqb  tmdpvol
1310101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1310200  3
1310201  0.0  0.9e6  300.0
.
