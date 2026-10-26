= 参考例: 泵自定义相似曲线(pump custom homologous curves) 稳态
* 部件: 源(tmdpvol 0.5MPa,300K) -> sngljun -> snglvol -> pump(自定义曲线) -> pipe(4体) -> sngljun -> 汇(tmdpvol 0.5MPa)
* 工况: 稳态 stdy-st
* 物理: 泵提供压头克服回路摩擦; 两端边界同压(0.5MPa), 流量由泵压头与阻力平衡决定
*       本例不用内置曲线(CCC0301 W1=-1/-2), 而是 W1=0 并随部件输入自定义单相相似曲线
*       结果: 流量25.7 kg/s, 泵吸入4.96MPa->排出5.16MPa(压头~0.2MPa, 与额定20m水柱一致)
* 关键坑1: CCC0301 W1=0 表示单相归一化表随部件输入; W1=-1(Bingham)/-2(Westinghouse)用内置
* 关键坑2: 16条曲线: 8条压头(H)+8条力矩(B); 曲线1=CCC1100-1199, 曲线2=CCC1200-1299, ..., 曲线16=CCC2600-2699
* 关键坑3: 每条曲线卡: W1=曲线类型(1=压头,2=力矩), W2=曲线工况(1..8), W3=自变量, W4=因变量
*          工况1(HAN/BAN)自变量v/α, 因变量h/α^2 或 β/α^2; 工况2(HVN/BVN)自变量α/v
* 关键坑4: 自变量范围 -1..0 或 0..1; 工况3,4,7,8(HAD/HVD/HAR/BAR)用负范围(-1..0), 否则报"indep. variable not within range"
* 关键坑5: 必须同时给压头曲线和力矩曲线(否则报"empty homologous curve type 2"); 建议给全16条
* 关键坑6: 泵是"控制体+两个接管"部件; 几何卡 CCC0101-0107(7项); CCC0108=吸入接管, CCC0109=排出接管
* 关键坑7: 泵吸入接管不能直接连到另一个接管, 必须连到控制体
* 已验证: 正常结束, 质量守恒(误差5.6e-4 kg), 节点进=出, 泵压头~0.2MPa
100  new  stdy-st
102  si  si
201  20.0  1.0e-6  0.01  3  100  200  500

1010000  inb  tmdpvol
1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1010200  3
1010201  0.0  5.0e5  300.0

1020000  inj  sngljun
1020101  101000000  105000000  0.02  0.0  0.0  0000
1020201  1  1.0  0.0  0.0

1050000  vol  snglvol
1050101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1050200  3  5.0e5  300.0

* pump component 110: control volume + suction junction + discharge junction
1100000  pmp  pump
1100101  0.02  0.5  0.01  0.0  0.0  0.0  0000
1100108  105010000  0.02  0.0  0.0  0000
1100109  120000000  0.02  0.0  0.0  0000
1100200  3  5.0e5  300.0
1100201  1  1.0  0.0  0.0
1100202  1  1.0  0.0  0.0
* W1=0 -> custom single-phase homologous curves supplied below
1100301  0  -1  -3  -1  -1  0  0
1100302  157.08  1.0  0.02  20.0  50.0  1.0  1000.0  0.0  0.0  0.0  0.0  0.0

* curve 1: head curve, condition 1 (HAN), v/alpha vs h/alpha^2
1101100  1  1  0.0  1.0
1101101  0.5  0.75
1101102  1.0  0.5
* curve 2: torque curve, condition 1 (BAN), v/alpha vs beta/alpha^2
1101200  2  1  0.0  1.0
1101201  0.5  0.6
1101202  1.0  0.3
* curve 3: head curve, condition 2 (HVN), alpha/v vs h/v^2
1101300  1  2  0.0  1.0
1101301  0.5  0.75
1101302  1.0  0.5
* curve 4: torque curve, condition 2 (BVN), alpha/v vs beta/v^2
1101400  2  2  0.0  1.0
1101401  0.5  0.6
1101402  1.0  0.3
* curve 5: head curve, condition 3 (HAD), negative range
1101500  1  3  -1.0  0.5
1101501  -0.5  0.75
1101502  0.0  1.0
* curve 6: torque curve, condition 3 (BAD), negative range
1101600  2  3  -1.0  0.3
1101601  -0.5  0.6
1101602  0.0  1.0
* curve 7: head curve, condition 4 (HVD), negative range
1101700  1  4  -1.0  0.5
1101701  -0.5  0.75
1101702  0.0  1.0
* curve 8: torque curve, condition 4 (BVD), negative range
1101800  2  4  -1.0  0.3
1101801  -0.5  0.6
1101802  0.0  1.0
* curve 9: head curve, condition 5 (HAT)
1101900  1  5  0.0  1.0
1101901  0.5  0.75
1101902  1.0  0.5
* curve 10: torque curve, condition 5 (BAT)
1102000  2  5  0.0  1.0
1102001  0.5  0.6
1102002  1.0  0.3
* curve 11: head curve, condition 6 (HAT)
1102100  1  6  0.0  1.0
1102101  0.5  0.75
1102102  1.0  0.5
* curve 12: torque curve, condition 6 (BAT)
1102200  2  6  0.0  1.0
1102201  0.5  0.6
1102202  1.0  0.3
* curve 13: head curve, condition 7 (HAR), negative range
1102300  1  7  -1.0  0.5
1102301  -0.5  0.75
1102302  0.0  1.0
* curve 14: torque curve, condition 7 (BAR), negative range
1102400  2  7  -1.0  0.3
1102401  -0.5  0.6
1102402  0.0  1.0
* curve 15: head curve, condition 8 (HAR), negative range
1102500  1  8  -1.0  0.5
1102501  -0.5  0.75
1102502  0.0  1.0
* curve 16: torque curve, condition 8 (BAR), negative range
1102600  2  8  -1.0  0.3
1102601  -0.5  0.6
1102602  0.0  1.0

1200000  pipe  pipe
1200001  4
1200101  0.02  4
1200301  0.25  4
1200601  0.0  4
1200801  4.5e-5  0.16  4
1201001  0000000  4
1201101  0  3
1201201  3  5.0e5  300.0  0  0  0  4
1201300  1
1201301  1.0  0.0  0.0  3

1300000  outj  sngljun
1300101  120010000  141000000  0.02  0.0  0.0  0000
1300201  1  1.0  0.0  0.0

1410000  outb  tmdpvol
1410101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1410200  3
1410201  0.0  5.0e5  300.0
.
