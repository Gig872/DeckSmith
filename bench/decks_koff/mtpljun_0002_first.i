= Branch flow splitter, steady state, 1 inlet 2 outlets
= Water 1.0 MPa 300 K from fixed-pressure source, splits into two legs
= Each leg: control volume + outlet junction to 0.5 MPa fixed-pressure sink
= Split junction areas 0.005 m2 each; adiabatic, no heating
*
100 new stdy-st
102 si si
201 10.0 1.0e-6 0.1 3 1 1 1
*
* --- source boundary: time dependent volume, 1.0 MPa, 300 K ---
1010000 source tmdpvol
1010101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1010200 3
1010201 0.0 1.0e6 300.0
*
* --- inlet junction: source -> branch inlet, area 0.01 ---
1020000 inlet tmdpjun
1020101 101010000 110000000 0.01
1020200 1
1020201 0.0 10.0 0.0 0.0
*
* --- BRANCH: 1 inlet (j1), 2 outlets (j2, j3) ---
1100000 brnch branch
1100001 3
1100101 0.01 0.5 0.005 0.0 0.0 0.0 0.0 0.1128 0
1100200 3 1.0e6 300.0
1100201 110000000 120000000 0.01 0.0 0.0 0
1100202 110000000 130000000 0.005 0.0 0.0 0
1100203 110000000 140000000 0.005 0.0 0.0 0
1100201 0.0 0.0
1100202 0.0 0.0
1100203 0.0 0.0
*
* --- leg 1 control volume ---
1200000 leg1 snglvol
1200101 0.01 0.5 0.005 0.0 0.0 0.0 0.0 0.1128 0
1200200 3 1.0e6 300.0
*
* --- leg 2 control volume ---
1300000 leg2 snglvol
1300101 0.01 0.5 0.005 0.0 0.0 0.0 0.0 0.1128 0
1300200 3 1.0e6 300.0
*
* --- outlet junction leg1 -> sink1 ---
1400000 outj1 sngljun
1400101 120010000 150010000 0.005 0.0 0.0 0
1400201 1 5.0 0.0 0.0
*
* --- outlet junction leg2 -> sink2 ---
1500000 outj2 sngljun
1500101 130010000 160010000 0.005 0.0 0.0 0
1500201 1 5.0 0.0 0.0
*
* --- sink 1: 0.5 MPa ---
1600000 sink1 tmdpvol
1600101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1600200 3
1600201 0.0 5.0e5 300.0
*
* --- sink 2: 0.5 MPa ---
1700000 sink2 tmdpvol
1700101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1700200 3
1700201 0.0 5.0e5 300.0
.
