= Steam turbine steady-state model
= Source: 3.0 MPa, 500 K superheated steam (tmdpvol)
= Artificial turbine (eta=0, isenthalpic) -> Main turbine (eta=0.7, r=0.5, R=0.5 m)
= Outlet: 0.3 MPa constant-pressure boundary
= Both turbines coupled to SHAFT control component
*
100 new stdy-st
102 si si
201 10.0 1.0e-6 0.1 3 1 1 1
*
* --- steam source boundary: 3.0 MPa, 500 K ---
1000000 source tmdpvol
1000101 0.05 0.5 0.025 0.0 0.0 0.0 0.0 0.0 0
1000200 3
1000201 0.0 3.0e6 500.0
*
* --- artificial turbine (eta=0, isenthalpic), required upstream of main turbine ---
1100000 arturb turbine
1100101 0.05 0.5 0.025 0.0 0.0 0.0 0.0 0.0 0
1100200 3 3.0e6 500.0
1100300 0.0 1.0 0.0 1 0 0
1100400 2 0.0 0.0 0.5
*
* --- main turbine (eta=0.7, reaction 0.5, mean stage radius 0.5 m) ---
1200000 mainturb turbine
1200101 0.05 0.5 0.025 0.0 0.0 0.0 0.0 0.0 0
1200200 3 3.0e6 500.0
1200300 0.0 1.0 0.0 1 0 0
1200400 2 0.7 0.5 0.5
*
* --- outlet boundary: 0.3 MPa ---
1300000 outlet tmdpvol
1300101 0.05 0.5 0.025 0.0 0.0 0.0 0.0 0.0 0
1300200 3
1300201 0.0 3.0e5 500.0
*
* --- junction: source -> artificial turbine (inlet, homogeneous, smooth) ---
1400000 jin1 sngljun
1400101 100000000 110000000 0.05 0.0 0.0 0
1400201 1 1.0 0.0 0.0
*
* --- junction: artificial turbine -> main turbine (inlet, homogeneous, smooth) ---
1500000 jin2 sngljun
1500101 110000000 120000000 0.05 0.0 0.0 0
1500201 1 1.0 0.0 0.0
*
* --- junction: main turbine -> outlet boundary (outlet, homogeneous, smooth) ---
1600000 jout sngljun
1600101 120000000 130010000 0.05 0.0 0.0 0
1600201 1 1.0 0.0 0.0
*
* --- SHAFT control component (205), coupled to both turbines ---
20500000 999
20500100 shaft SHAFT 1.0 0.0 0 0
20500101 0 1.0 0.0 TURBINE 110
20500102 0 1.0 0.0 TURBINE 120
.
