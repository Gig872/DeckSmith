= Point-kinetics-driven heated channel, steady state
= Coolant: water 15.0 MPa, 560 K, 8 kg/s through a 4-volume round pipe
= Pipe: area 0.01 m2, total length 2 m (4 x 0.5 m), horizontal
= Fuel rod heat structure: cylindrical, OD 79.6 mm, wall 0.6 mm, 4 axial segments
=   (rod sized so surface heat flux ~1 MW/m2, a realistic PWR-like value)
= Heat source: total reactor power 0.5 MW (general table POWER, 0.25 per segment)
= PK parameters (recorded, not dynamically active in steady state):
=   beta=0.0065, Lambda=1e-4 s, rho0=0
= Expected: outlet ~571 K, void fraction ~0 (subcooled liquid)
*
100 new stdy-st
102 si si
201 10.0 1.0e-6 0.1 3 1 1 1
*
* --- source boundary: time dependent volume, 15 MPa, 560 K ---
1010000 source tmdpvol
1010101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1010200 3
1010201 0.0 1.5e7 560.0
*
* --- inlet: time dependent junction, 8 kg/s from source into pipe inlet ---
1020000 inlet tmdpjun
1020101 101010000 120000000 0.01
1020200 1
1020201 0.0 8.0 0.0 0.0
*
* --- heated channel: 4 volumes, area 0.01, length 0.5 m each, horizontal ---
1200000 pipe pipe
1200001 4
1200101 0.01 1
1200102 0.01 2
1200103 0.01 3
1200104 0.01 4
1200301 0.5 1
1200302 0.5 2
1200303 0.5 3
1200304 0.5 4
1200601 0.0 1
1200602 0.0 2
1200603 0.0 3
1200604 0.0 4
1200801 4.5e-5 0.1128 1
1200802 4.5e-5 0.1128 2
1200803 4.5e-5 0.1128 3
1200804 4.5e-5 0.1128 4
1201001 0 1
1201002 0 2
1201003 0 3
1201004 0 4
1201101 0 1
1201102 0 2
1201103 0 3
1201201 3 1.5e7 560.0 0 0 0 1
1201202 3 1.5e7 560.0 0 0 0 2
1201203 3 1.5e7 560.0 0 0 0 3
1201204 3 1.5e7 560.0 0 0 0 4
1201300 1
1201301 8.0 0.0 0.0 1
1201302 8.0 0.0 0.0 2
1201303 8.0 0.0 0.0 3
*
* --- outlet boundary: time dependent volume, 15 MPa sink ---
1300000 outlet tmdpvol
1300101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1300200 3
1300201 0.0 1.5e7 560.0
*
* --- junction: pipe outlet to outlet boundary ---
1400000 outjun sngljun
1400101 120010000 130010000 0.01 0.0 0.0 0
1400201 1 8.0 0.0 0.0
*
* --- fuel rod heat structure (cylindrical), 4 axial segments ---
11500000 4 2 2 0 0.0392 0 0 4
11500100 0 1
11500101 1 0.0398
11500201 1 1
11500301 1.0 1
11500401 560.0 1 560.0 2
11500701 1 0.25 0.0 0.0 1
11500702 1 0.25 0.0 0.0 2
11500703 1 0.25 0.0 0.0 3
11500704 1 0.25 0.0 0.0 4
11500801 0.0 10.0 10.0 0.0 0.0 0.0 0.0 1.0 1
11500802 0.0 10.0 10.0 0.0 0.0 0.0 0.0 1.0 2
11500803 0.0 10.0 10.0 0.0 0.0 0.0 0.0 1.0 3
11500804 0.0 10.0 10.0 0.0 0.0 0.0 0.0 1.0 4
11500501 120010000 0 1 1 0.5 1
11500502 120020000 0 1 1 0.5 2
11500503 120030000 0 1 1 0.5 3
11500504 120040000 0 1 1 0.5 4
11500601 0 0 0 1 0.5 1
11500602 0 0 0 1 0.5 2
11500603 0 0 0 1 0.5 3
11500604 0 0 0 1 0.5 4
*
* --- general table 1: total reactor power vs time (constant 0.5 MW) ---
20200100 power
20200101 0.0 5.0e5
20200102 100.0 5.0e5
*
* --- thermal properties: material 1 = UO2 (built-in) ---
20100100 uo2
.
