= NOZZLE CRITICAL (CHOKED) FLOW - STEADY STATE
= 3.0 MPa / 487 K subcooled water -> 1.18 m, ID 0.05 m pipe (4 CV) -> 0.1 MPa atmosphere
= area = pi*0.05^2/4 = 1.9635e-3 m2 ; each CV length = 1.18/4 = 0.295 m ; roughness 4.5e-5 m
100  new  stdy-st
102  si  si
201  2.0  1.0e-8  2.0e-4  3  1000  5000  5000
*
* --- upstream constant-pressure source: 3.0 MPa, 487 K subcooled water
1010000  upsrc  tmdpvol
1010101  1.9635e-3  0.2  3.927e-4  0.0  0.0  0.0  0.0  0.05  0000
1010200  3
1010201  0.0  3.0e6  487.0
*
* --- nozzle pipe: 4 control volumes, horizontal, constant area 0.05 m ID
1100000  nozzle  pipe
1100001  4
1100101  1.9635e-3  4
1100301  0.295  4
1100601  0.0  4
1100801  4.5e-5  0.05  4
1101001  0000000  4
1101101  0  3
1101201  3  3.00e6  487.0  0.0  0.0  0.0  1
1101202  3  2.95e6  487.0  0.0  0.0  0.0  2
1101203  3  2.80e6  487.0  0.0  0.0  0.0  3
1101204  3  2.50e6  487.0  0.0  0.0  0.0  4
1101300  1
1101301  70.0  0.0  0.0  3
*
* --- inlet junction from source to nozzle (area = pipe area, no area change)
1200000  inljun  sngljun
1200101  101010000  110000000  1.9635e-3  0.0  0.0  0000
1200201  1  70.0  0.0  0.0
*
* --- outlet junction from nozzle to atmosphere sink (choked-flow model active)
1300000  outjun  sngljun
1300101  110010000  150000000  1.9635e-3  0.0  0.0  0000
1300201  1  70.0  0.0  0.0
*
* --- downstream back-pressure boundary: 0.1 MPa atmosphere
1500000  atm  tmdpvol
1500101  1.9635e-3  0.2  3.927e-4  0.0  0.0  0.0  0.0  0.05  0000
1500200  3
1500201  0.0  1.0e5  373.0
.
