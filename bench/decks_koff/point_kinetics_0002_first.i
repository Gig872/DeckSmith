= Point-kinetics driven heated channel, steady state
= Water 15.0 MPa 560 K, 5 kg/s through 4-volume round pipe (A=0.01 m2, L=2 m)
= Cylindrical fuel rod heat structure, heat source = total reactor power (type 1000)
= Point kinetics: total power 0.5 MW, rho0=0, beta=0.0065, neutron lifetime 1e-4 s
*
100 new transnt
102 si si
201 20.0 1.0e-6 0.05 3 1 1 1
*
* --- point reactor kinetics ---
30000000 point separabl
30000001 no-gamma 5.0e5 0.0 0.0065 1.0e-4
30000101 0.000215 0.0124 1
30000102 0.001424 0.0305 2
30000103 0.001274 0.111 3
30000104 0.002568 0.301 4
30000105 0.000748 1.14 5
30000106 0.000273 3.01 6
*
* --- inlet boundary: time dependent junction, 5 kg/s mass flow ---
1000000 inlet tmdpjun
1000101 100010000 120010000 0.01
1000200 1
1000201 0.0 5.0 0.0 0.0
*
* --- heated channel: 4 volumes, area 0.01, total length 2 m, horizontal ---
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
1201201 3 15.0e6 560.0 0 0 0 1
1201202 3 15.0e6 560.0 0 0 0 2
1201203 3 15.0e6 560.0 0 0 0 3
1201204 3 15.0e6 560.0 0 0 0 4
1201300 1
1201301 20.0 0.0 0.0 1
1201302 20.0 0.0 0.0 2
1201303 20.0 0.0 0.0 3
*
* --- outlet boundary: time dependent volume, 15 MPa, 560 K ---
1300000 outlet tmdpvol
1300101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1300200 3
1300201 0.0 15.0e6 560.0
*
* --- junction: pipe outlet to outlet boundary ---
1400000 outjun sngljun
1400101 120010000 130010000 0.01 0.0 0.0 0
1400201 1 5.0 0.0 0.0
*
* --- heat structure: cylindrical fuel rod, 4 axial nodes ---
* general: NH=4 axial, NP=4 radial, geometry=2 (cylindrical), steady init=1
12010000 fuelrod 2
12010001 4 4 2 1 0.0 0 0 4
* radial mesh: fuel r=0..0.004, gap 0.004..0.0041, clad 0.0041..0.00475
12010100 0 2
12010101 0.004 1
12010102 0.0001 2
12010103 0.00065 3
* composition: 1=fuel, 2=gap, 3=clad
12010201 1 1
12010202 2 2
12010203 3 3
* initial temperature 560 K at all 4 radial nodes
12010400 0
12010401 560.0 1
12010402 560.0 2
12010403 560.0 3
12010404 560.0 4
* left boundary: adiabatic (centerline)
12010501 0 0 0 0.0 1
* right boundary: convective to pipe volumes 1-4
12010601 120010000 1 1 0 0.00475 1
12010602 120020000 1 1 0 0.00475 2
12010603 120030000 1 1 0 0.00475 3
12010604 120040000 1 1 0 0.00475 4
* heat source: type 1000 = total reactor power, multiplier 1.0
12010701 1000 1.0 0.0 0.0 1
12010702 1000 1.0 0.0 0.0 2
12010703 1000 1.0 0.0 0.0 3
12010704 1000 1.0 0.0 0.0 4
*
* --- thermal properties: fuel (UO2-like), gap, cladding ---
20100100 tbl/fctn 1 1
20100101 1.0
20100200 tbl/fctn 1 1
20100201 0.3
20100300 tbl/fctn 1 1
20100301 16.0
*
* --- volumetric heat capacity (rho*cp) for each composition ---
20100110 3.0e6
20100210 1.0e6
20100310 3.2e6
.
