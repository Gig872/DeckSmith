= Jet mixer steady-state model
= Drive source 1.0 MPa, suction source 0.9 MPa, discharge 0.5 MPa
= Mixer flow area 0.005 m2, water at 300 K
*
* --- control cards ---
100 new stdy-st
102 si si
201 1.0 1.0e-6 0.1 3 1 1 0
*
* --- drive source: time dependent volume, 1.0 MPa, 300 K ---
1100000 drvsrc tmdpvol
1100101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1100200 3
1100201 0.0 1.0e6 300.0
*
* --- suction source: time dependent volume, 0.9 MPa, 300 K ---
1200000 suctsrc tmdpvol
1200101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1200200 3
1200201 0.0 9.0e5 300.0
*
* --- mixer chamber: single volume, area 0.005 m2 ---
1300000 mixer snglvol
1300101 0.005 0.1 5.0e-4 0.0 0.0 0.0 0.0 0.0 0
1300200 3 7.0e5 300.0
*
* --- discharge boundary: time dependent volume, 0.5 MPa, 300 K ---
1400000 outlet tmdpvol
1400101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1400200 3
1400201 0.0 5.0e5 300.0
*
* --- drive junction: drive source -> mixer ---
1500000 drvjun sngljun
1500101 110010000 130000000 0.005 0.0 0.0 0
1500201 0 0.0 0.0 0.0
*
* --- suction junction: suction source -> mixer ---
1600000 sucjun sngljun
1600101 120010000 130000000 0.005 0.0 0.0 0
1600201 0 0.0 0.0 0.0
*
* --- discharge junction: mixer -> outlet ---
1700000 outjun sngljun
1700101 130010000 140010000 0.005 0.0 0.0 0
1700201 0 0.0 0.0 0.0
.
