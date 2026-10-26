= Jet mixer steady-state model
= Drive source 1.0 MPa, suction source 0.8 MPa, outlet 0.7 MPa
= Mixing volume area 0.005 m2; water ~300 K
= Goal: steady flow split (drive flow vs suction flow)
*
100 new stdy-st
102 si si
201 10.0 1.0e-6 0.1 3 1 1 1
*
* --- drive source boundary: 1.0 MPa, 300 K ---
1000000 drive tmdpvol
1000101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1000200 3
1000201 0.0 1.0e6 300.0
*
* --- suction source boundary: 0.8 MPa, 300 K ---
1100000 suct tmdpvol
1100101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1100200 3
1100201 0.0 8.0e5 300.0
*
* --- mixing volume: area 0.005 m2, length 0.2 m ---
1200000 mixer snglvol
1200101 0.005 0.2 0.001 0.0 0.0 0.0 0.0 0.0 0
1200200 3 7.5e5 300.0
*
* --- outlet boundary: 0.7 MPa, 300 K ---
1300000 outlet tmdpvol
1300101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1300200 3
1300201 0.0 7.0e5 300.0
*
* --- drive junction: drive source -> mixer (nozzle, area 0.001, K=1) ---
1400000 drvjun sngljun
1400101 100000000 120000000 0.001 1.0 1.0 0
1400201 1 1.0 0.0 0.0
*
* --- suction junction: suction source -> mixer (area 0.001, K=1) ---
1500000 sucjun sngljun
1500101 110000000 120000000 0.001 1.0 1.0 0
1500201 1 1.0 0.0 0.0
*
* --- outlet junction: mixer -> outlet boundary (area 0.005, K=1) ---
1600000 outjun sngljun
1600101 120000000 130010000 0.005 1.0 1.0 0
1600201 1 1.0 0.0 0.0
.
