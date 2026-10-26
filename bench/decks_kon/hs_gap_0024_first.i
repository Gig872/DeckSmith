= 燃料棒热构件稳态传热模型 (fuel rod, 3-layer, gap conduction)
* 场景: 15.5 MPa / 560 K 过冷水, 0.5 kg/s 定流量通过单控制体通道
* 通道外耦合圆柱形燃料棒: 燃料(0-4.0mm) / 氦间隙(4.0-4.1mm,1.0MPa) / 包壳(4.1-4.7mm)
* 燃料内均匀裂变热源 80 kW, 间隙传导模型, 稳态
* 驱动: 入口 tmdpjun 定流量 0.5 kg/s, 出口 tmdpvol 定压 15.5 MPa (进=出)
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
1020201  0.0  0.5  0.0  0.0

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
1200201  1  0.5  0.0  0.0

1510000  outb  tmdpvol
1510101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1510200  3
1510201  0.0  1.55e7  560.0

* heat structure HS 110, geometry 1: NH=1 NP=4 cylinder steady=0 leftcoord=0
11101000  1  4  2  0  0.0  0  0  4
* gap conduction: initial gap pressure 1.0 MPa, reference volume 110010000
11101001  1.0e6  110010000
* gap deformation: fuel rough, clad rough, fuel disp, clad creep, HS no.
11101011  1.0e-6  2.0e-6  0.0  0.0  1
11101100  0  1
* radial intervals (format1: W1=#intervals, W2=right coord m)
11101101  1  0.004
11101102  1  0.0041
11101103  1  0.0047
* composition: interval1=fuel(1), interval2=gap(2), interval3=clad(3)
11101201  1  1
11101202  2  2
11101203  3  3
* radial power: interval1=1.0, others 0
11101301  1.0  1
11101302  0.0  2
11101303  0.0  3
* heat source: type1 (table 1), multiplier 1.0, HS 1
11101701  1  1.0  0.0  0.0  1
* initial temperature 560 K all 4 nodes
11101400  0
11101401  560.0  1
11101402  560.0  2
11101403  560.0  3
11101404  560.0  4
* left boundary: adiabatic symmetry
11101501  0  0  0  0  0.0  1
* right boundary: convective, vol 110010000, type 1
11101601  110010000  0  1  1  1.0  1
* additional left/right boundary cards
11101801  0.1128  10.0  10.0  0.0  0.0  0.0  0.0  1.0  1
11101901  0.1128  10.0  10.0  0.0  0.0  0.0  0.0  1.0  1

* material 1: UO2 fuel (built-in)
20100100  uo2
* material 2: helium gap gas (W2=3 gap material, W3=1)
20100200  tbl/fctn  3  1
20100201  helium  1.0
20100251  300.0  1.0e5
20100252  3000.0  1.0e5
* material 3: zirconium cladding (built-in)
20100300  zr

* power table: 80 kW constant
20200100  power
20200101  0.0  8.0e4
20200102  100.0  8.0e4
.
