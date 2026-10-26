= Steam turbine steady-state model
= Source 3.0 MPa 500 K -> dummy turbine (eta=0) -> main turbine (eta=0.85, r=0.5, R=0.5 m)
= -> exhaust boundary 0.3 MPa 500 K; turbines coupled to SHAFT
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
* --- junction: source to dummy turbine inlet ---
1100000 injun sngljun
1100101 100010000 120000000 1.0 0.0 0.0 0
1100201 0 0.0 0.0 0.0
*
* --- dummy (artificial) turbine: eta=0, isenthalpic ---
1200000 dturb turbine
1200001 1
1200101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1200200 3 3.0e6 500.0
1200201 1 1.0 0.0 0.0
1200300 0.0 1.0 0.0 0
1200400 1 0.0 0.0 0.5
*
* --- junction: dummy turbine outlet to main turbine inlet ---
1300000 midjun sngljun
1300101 120010000 140000000 1.0 0.0 0.0 0
1300201 0 0.0 0.0 0.0
*
* --- main turbine: eta=0.85, reaction 0.5, mean stage radius 0.5 m ---
1400000 mturb turbine
1400001 1
1400101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1400200 3 3.0e6 500.0
1400201 1 1.0 0.0 0.0
1400300 0.0 1.0 0.0 1
1400400 1 0.85 0.5 0.5
*
* --- junction: main turbine outlet to exhaust boundary ---
1500000 outjun sngljun
1500101 140010000 160000000 1.0 0.0 0.0 0
1500201 0 0.0 0.0 0.0
*
* --- exhaust boundary: time dependent volume, 0.3 MPa, 500 K ---
1600000 exhaust tmdpvol
1600101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1600200 3
1600201 0.0 3.0e5 500.0
*
* --- shaft control component (control variable 1) ---
20500000 999
20500100 shaft SHAFT 1.0 0.0 0
20500101 0 1.0 0.0 TURBINE 120
20500102 0 1.0 0.0 TURBINE 140
.
