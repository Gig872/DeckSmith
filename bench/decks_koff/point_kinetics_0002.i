= Point-kinetics driven heated channel, steady state
= Water 15.0 MPa 560 K, 5 kg/s through 4-volume round pipe (A=0.01 m2, L=2 m)
= Cylindrical fuel rod heat structure, heat source = total reactor power (type 1000)
= Point kinetics: total power 0.5 MW, rho0=0, beta=0.0065, neutron lifetime 1e-4 s
*
100 new transnt
102 si si
201 200.0 1.0e-6 0.05 3 1 1 1
*
* --- point reactor kinetics ---
30000000 point separabl
30000001 no-gamma 5.0e5 0.0 0.0065 1.0e-4
30000101 0.033077 0.0124
30000102 0.219077 0.0305
30000103 0.196000 0.111
30000104 0.395077 0.301
30000105 0.115077 1.14
30000106 0.041692 3.01
*
* --- inlet boundary: time dependent volume (state) + tmdpjun (5 kg/s flow) ---
1000000 inbnd tmdpvol
1000101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1000200 3
1000201 0.0 15.0e6 560.0
*
1100000 inlet tmdpjun
1100101 100010000 120000000 0.01
1100200 1
1100201 0.0 5.0 0.0 0.0
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
1201301 0.666 0.0 0.0 1
1201302 0.666 0.0 0.0 2
1201303 0.666 0.0 0.0 3
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
* --- heat structure: cylindrical fuel rod (equivalent rod-bundle), 4 axial nodes ---
* general: NH=4 axial, NP=3 radial, geometry=2 (cylindrical), steady init=0
11201000 4 3 2 0 0.0 0 0 4
* radial mesh: solid rod r=0..0.04 m (equivalent heated perimeter for ~1 MW/m2)
11201100 0 2
11201101 0.02 1
11201102 0.02 2
* composition: 1=rod (metallic, high conductivity)
11201201 1 1
11201202 1 2
* heat source distribution (radial): uniform
11201301 1.0 1
11201302 1.0 2
* initial temperature 560 K at all 3 radial nodes
11201400 0
11201401 560.0 1
11201402 560.0 2
11201403 560.0 3
* left boundary: adiabatic (inner surface)
11201501 0 0 0 0 0.0 1 0 0 0 0 0.0 2 0 0 0 0 0.0 3 0 0 0 0 0.0 4
* right boundary: convective to pipe volumes 1-4
11201601 120010000 1 1 0 0.04 1
11201602 120020000 1 1 0 0.04 2
11201603 120030000 1 1 0 0.04 3
11201604 120040000 1 1 0 0.04 4
* additional right boundary data (CHF correlation): 9 words per group
11201901 0.08 1.0 1.0 0.0 0.0 0.0 0.0 1.0 1
11201902 0.08 1.0 1.0 0.0 0.0 0.0 0.0 1.0 2
11201903 0.08 1.0 1.0 0.0 0.0 0.0 0.0 1.0 3
11201904 0.08 1.0 1.0 0.0 0.0 0.0 0.0 1.0 4
* heat source: type 1000 = total reactor power, axial multiplier 0.25 each (sum=1)
11201701 1000 0.25 0.0 0.0 1
11201702 1000 0.25 0.0 0.0 2
11201703 1000 0.25 0.0 0.0 3
11201704 1000 0.25 0.0 0.0 4
*
* --- thermal properties: rod material (ZR, k~16 W/m-K) ---
20100100 zr
.
