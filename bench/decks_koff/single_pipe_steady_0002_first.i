= Horizontal circular pipe: steady flow + uniform wall heating
= Area 0.02 m2, L=1.0 m, 4 volumes, roughness 4.5e-5 m, Dh=0.1596 m
= Inlet 2.0 kg/s @300 K, outlet 1.0 MPa, total power 100000 W
*
100 new stdy-st
102 si si
201 1.0 1.0e-6 0.1 3
*
* --- Inlet flow boundary: time-dependent junction (mass flow) ---
1010000 inlet tmdpjun
1010101 0 110010000 0.02
1010200 1
1010201 0.0 2.0 0.0 0.0
*
* --- Outlet pressure boundary: time-dependent volume ---
1020000 outlet tmdpvol
1020101 0.02 1.0 0.02 0.0 0.0 0.0 0.0 0.1596 0
1020200 3
1020201 0.0 1.0e6 300.0
*
* --- Pipe: 4 volumes ---
1100000 pipe pipe
1100001 4
1100101 0.02 4
1100301 0.25 4
1100601 0.0 4
1100801 4.5e-5 0.1596 4
1101001 0 4
1101101 0 3
1101201 3 1.0e6 300.0 0 0 0 4
1101300 1
1101301 2.0 2.0 0.0 3
*
* --- Junction: inlet tmdpjun -> pipe inlet ---
1110000 inj sngljun
1110101 101010000 110000000 0.02 0.0 0.0 0
1110201 1 2.0 0.0 0.0
*
* --- Junction: pipe outlet -> outlet tmdpvol ---
1120000 outj sngljun
1120101 110010000 102010000 0.02 0.0 0.0 0
1120201 1 2.0 0.0 0.0
*
* --- Heat structure: 4 axial nodes, 1 radial node, rectangular ---
1200000 hs1 heat-struct
1200001 4 2 1 0 0.0 0 0 4
1200100 0 2
1200101 0.005 1
1200201 1 1
1200301 1.0 1
1200400 0
1200401 300.0 2
1200501 0 0 0.0 0 0.0 1
1200502 0 0 0.0 0 0.0 2
1200503 0 0 0.0 0 0.0 3
1200504 0 0 0.0 0 0.0 4
1200601 0 0 0.0 0 0.0 1
1200602 0 0 0.0 0 0.0 2
1200603 0 0 0.0 0 0.0 3
1200604 0 0 0.0 0 0.0 4
1200701 0 1.0 0.0 0.0 1
1200702 0 1.0 0.0 0.0 2
1200703 0 1.0 0.0 0.0 3
1200704 0 1.0 0.0 0.0 4
*
* --- Heat structure left boundary: coupled to pipe volumes 1-4 ---
1200501 110010000 0 1 0.0 0.0 1
1200502 110020000 0 1 0.0 0.0 2
1200503 110030000 0 1 0.0 0.0 3
1200504 110040000 0 1 0.0 0.0 4
*
* --- Power table: total 100000 W ---
20200000 power
20200001 0.0 100000.0
20200002 1.0 100000.0
*
.
