= Steam turbine steady-state model
= Source: 3.0 MPa, 500 K (tmdpvol)
= Artificial turbine (h=0, isenthalpic) -> main turbine (eta=0.7, reaction=0.5, R=0.5 m)
= Exhaust to 0.5 MPa, 500 K pressure boundary (tmdpvol)
= Turbine coupled to SHAFT control component
*
100 new stdy-st
102 si si
201 10.0 1.0e-6 0.1 3 1 1 1
*
* --- steam source: time dependent volume, 3.0 MPa, 500 K ---
1000000 source tmdpvol
1000101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1000200 3
1000201 0.0 3.0e6 500.0
*
* --- artificial turbine (isenthalpic, eta=0), upstream of main turbine ---
1100000 arturb turbine
1100101 0.1 0.5 0.05 0.0 0.0 0.0 0.0 0.0 0
1100200 3 3.0e6 500.0
1100201 100000000 0.1 0.0 0.0 0
1100300 157.08 0.5 0.0 1 0 0
1100400 2 0.0 0.5 0.5
*
* --- main turbine (eta=0.7, reaction=0.5, R=0.5 m) ---
1200000 mainturb turbine
1200101 0.1 0.5 0.05 0.0 0.0 0.0 0.0 0.0 0
1200200 3 3.0e6 500.0
1200201 110010000 0.1 0.0 0.0 0
1200300 157.08 1.0 0.0 1 0 0
1200400 2 0.7 0.5 0.5
*
* --- exhaust boundary: time dependent volume, 0.5 MPa, 500 K ---
1300000 exhaust tmdpvol
1300101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1300200 3
1300201 0.0 5.0e5 500.0
*
* --- junction: main turbine outlet to exhaust boundary ---
1400000 outjun sngljun
1400101 120010000 130010000 0.1 0.0 0.0 0
1400201 1 20.0 0.0 0.0
*
* --- SHAFT control component (turbine shaft) ---
20500000 999
20500100 shaft shaft 1.0 157.08 0
20500101 0 1.0 0.0 turbine 110
20500102 0 1.0 0.0 turbine 120
.
