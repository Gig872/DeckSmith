* Upward vertical single-volume steady-state heating model
* SI units, stdy-st
*
100  new  stdy-st
102  si  si
201  10.0  1.0e-6  1.0  3  100  200  500
*
* Single control volume: A=0.01 m2, L=2.0 m, angle=90 deg, dz=1.0 m
1200000  VOL1  snglvol
1200101  0.01  2.0  0.02  0.0  90.0  1.0  4.5e-5  0.1128  0
1200200  3  1.0e6  300.0  400000.0
*
* INLET: sngljun, connects to VOL1 inlet (0 -> 1200000)
1100000  INLET  sngljun
1100101  0  120000000  0.01  0.0  0.0  0000
1100200  1
1100201  20.0  0.0  0.0
*
* OUTLET: tmdpvol, at VOL1 outlet (120000001)
1300000  OUTLET  tmdpvol
1300101  0.01  2.0  0.0  0.0  90.0  1.0  0.0  4.5e-5  0.1128  0000
1300200  3
1300201  0.0  1.0e6  305.0
*
.