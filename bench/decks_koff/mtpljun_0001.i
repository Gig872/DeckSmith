= Branch flow splitter: 1 inlet, 2 outlets, steady state
= Water 1.0 MPa, 300 K from source, split into two legs, each to 0.3 MPa sink
= Branch outlet junction areas = 0.005 m2 each
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
* --- branch: 1 inlet (j1 from source), 2 outlets (j2, j3) ---
1100000 brnch branch
1100001 3
1100101 0.01 0.5 0.005 0.0 0.0 0.0 0.0 0.0 0
1100200 3 1.0e6 300.0
1101101 101010000 110000000 0.01 0.0 0.0 0
1102101 110000000 120000000 0.005 0.0 0.0 1
1103101 110000000 130000000 0.005 0.0 0.0 1
1101201 0.0 0.0
1102201 0.0 0.0
1103201 0.0 0.0
*
* --- leg 1 control volume ---
1200000 leg1 snglvol
1200101 0.01 0.5 0.005 0.0 0.0 0.0 0.0 0.0 0
1200200 3 1.0e6 300.0
*
* --- leg 2 control volume ---
1300000 leg2 snglvol
1300101 0.01 0.5 0.005 0.0 0.0 0.0 0.0 0.0 0
1300200 3 1.0e6 300.0
*
* --- leg 1 outlet junction: leg1 -> sink1 ---
1400000 out1 sngljun
1400101 120010000 141010000 0.005 0.0 0.0 0
1400201 1 10.0 0.0 0.0
*
* --- leg 2 outlet junction: leg2 -> sink2 ---
1500000 out2 sngljun
1500101 130010000 151010000 0.005 0.0 0.0 0
1500201 1 10.0 0.0 0.0
*
* --- sink 1 boundary: 0.3 MPa ---
1410000 sink1 tmdpvol
1410101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1410200 3
1410201 0.0 3.0e5 300.0
*
* --- sink 2 boundary: 0.3 MPa ---
1510000 sink2 tmdpvol
1510101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1510200 3
1510201 0.0 3.0e5 300.0
.
