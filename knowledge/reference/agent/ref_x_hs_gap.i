= 参考例: 热构件高级模型 - 间隙传导(gap conduction) 稳态
* 部件: tmdpvol(15.5MPa,560K) -> tmdpjun(0.3kg/s) -> pipe(1体,燃料通道) -> sngljun -> tmdpvol(15.5MPa)
*       燃料棒热构件(圆柱,含燃料-间隙-包壳三层) 通过间隙传导把裂变热传给冷却剂
* 工况: 稳态 stdy-st, 100s
* 物理: 燃料棒内热源(裂变50kW) -> 燃料导热 -> 间隙(氦气)传导 -> 包壳导热 -> 对流给冷却剂
*       间隙传导模型: 间隙内气体压力 P(t)=P(0)/T(0)*T(t), 间隙导热系数随间隙尺寸/气体变化
*       结果: 冷却剂560K->589.6K, 间隙9.16e-5m, 包壳半径4.70e-3m, 间隙压力1.0MPa
* 关键坑1: 间隙传导模型必须用圆柱几何(W3=2); 必须输入 1CCCG001 卡(初始间隙压力+参考控制体)
* 关键坑2: 1CCCG100 的 W1 必须为0(几何数据随热构件输入)
* 关键坑3: 1CCCG011-099 间隙变形数据(5项): 燃料表面粗糙度 包壳表面粗糙度 燃料径向位移 包壳蠕变位移 热构件号
* 关键坑4: 1CCCG201-299 组成数据: 组成号 间隔号; 间隙间隔用间隙材料号
* 关键坑5: 201MMM00 卡 W2 必须为3(间隙材料), W3 也要给(体积热容标识); 201MMM01-49 给气体名+克分子份额;
*          201MMM51-99 给体积热容表(否则报"Cards 201MMM51-299 missing")
* 关键坑6: 内置材料名只有 CC-STEEL/S-STEEL/UO2/ZR; 写 zircaloy 会报"Composition type unrecognizable"
* 关键坑7: 径向间隔卡 1CCCG101-199 格式1: W1=该区间隔数(不是间隔号!), W2=右坐标; 写错会报"mesh spacings inconsistent"
* 关键坑8: 间隙模型要求右边界卡 1CCCG601-699 的 W1 给边界控制体号; 且不能同时用绝热(type0)+边界体
* 关键坑9: 用了间隙模型必须给 1CCCG901-999 附加右边界卡
* 关键坑10: 径向网格 NP=4: 燃料中心 燃料表面 包壳内 包壳外; 间隙在燃料表面与包壳内之间
* 已验证: 正常结束, 质量守恒(误差7.7e-4 kg), 节点进=出, 间隙模型激活
100  new  stdy-st
102  si  si
201  100.0  1.0e-6  0.01  3  100  200  500

1010000  inb  tmdpvol
1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1010200  3
1010201  0.0  1.55e7  560.0

1020000  inj  tmdpjun
1020101  101000000  110000000  0.01
1020200  1
1020201  0.0  0.3  0.0  0.0

1100000  pipe  pipe
1100001  1
1100101  0.01  1
1100301  1.0  1
1100601  0.0  1
1100801  4.5e-5  0.1128  1
1101001  0000000  1
1101201  3  1.55e7  560.0  0  0  0  1

1200000  outj  sngljun
1200101  110010000  151000000  0.01  0.0  0.0  0000
1200201  1  0.3  0.0  0.0

1510000  outb  tmdpvol
1510101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1510200  3
1510201  0.0  1.55e7  560.0

* heat structure: HS 110, geometry 1, fuel rod with gap, coupled to pipe 110 (1 axial segment)
* NH=1, NP=4 (fuel center, fuel surface, clad inner, clad outer), cylinder, steady init, left coord 0
11101000  1  4  2  0  0.0  0  0  4
* gap conduction model: initial gap pressure 1.0e6 Pa, reference volume 110010000
11101001  1.0e6  110010000
* gap deformation data: fuel roughness, clad roughness, fuel radial disp, clad creep disp, HS no.
11101011  1.0e-6  2.0e-6  0.0  0.0  1
* network flag W1=0 (geometry data included)
11101100  0  1
* radial intervals (format 1: W1=number of intervals in region, W2=right coordinate)
* region 1 (fuel) 1 interval to 0.004, region 2 (gap) 1 interval to 0.0041, region 3 (clad) 1 interval to 0.0047
11101101  1  0.004
11101102  1  0.0041
11101103  1  0.0047
* composition: interval 1 = fuel (mat 1), interval 2 = gap (mat 2), interval 3 = clad (mat 3)
11101201  1  1
11101202  2  2
11101203  3  3
* radial power distribution (peaking factors): interval 1 = 1.0, interval 2,3 = 0
11101301  1.0  1
11101302  0.0  2
11101303  0.0  3
* heat source: type 1 (power table), multiplier 1.0, HS 1
11101701  1  1.0  0.0  0.0  1
* initial temperature: 560 K at all 4 nodes
11101400  0
11101401  560.0  1
11101402  560.0  2
11101403  560.0  3
11101404  560.0  4
* left boundary: coupled to pipe vol 110010000, convective, surface code 1 (cylinder height)
11101501  110010000  0  1  1  1.0  1
* right boundary: gap model needs a boundary volume number; use pipe vol, type 1000 (surface temp = vol temp)
11101601  110010000  0  1000  1  1.0  1
* additional left boundary card
11101801  0.1128  10.0  10.0  0.0  0.0  0.0  0.0  1.0  1
* additional right boundary card
11101901  0.1128  10.0  10.0  0.0  0.0  0.0  0.0  1.0  1

* power table: 50 kW constant
20200100  power
20200101  0.0  5.0e4
20200102  100.0  5.0e4

* material 1: fuel (UO2 built-in)
20100100  uo2
* material 2: gap gas (helium) - W2=3 for gap material, gas composition table
20100200  tbl/fctn  3  1
20100201  helium  1.0
20100251  300.0  1.0e5
20100252  3000.0  1.0e5
* material 3: cladding (zirconium built-in)
20100300  zr
.
