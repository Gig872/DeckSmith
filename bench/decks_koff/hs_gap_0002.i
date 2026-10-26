= Fuel rod steady-state heat conduction with gap conductance model
= Coolant: water 15.5 MPa, 560 K, 0.3 kg/s through a single-volume channel
= Fuel rod (cylindrical): UO2 fuel 0-4.0 mm, He gap 4.0-4.1 mm @ 0.5 MPa, cladding 4.1-4.7 mm
= Heat source: 30 kW uniform fission power in the fuel
= Expected: coolant dT = Q/(m*cp) = 30000/(0.3*5500) ~ 18 K -> outlet ~578 K
*
100 new stdy-st
102 si si
201 200.0 1.0e-6 0.5 3 1 1 1
*
* --- source boundary: time dependent volume, 15.5 MPa, 560 K ---
1010000 source tmdpvol
1010101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1010200 3
1010201 0.0 1.55e7 560.0
*
* --- inlet: time dependent junction, 0.3 kg/s from source into channel ---
1020000 inlet tmdpjun
1020101 101010000 120000000 0.01
1020200 1
1020201 0.0 0.3 0.0 0.0
*
* --- coolant channel: single volume, area 0.01 m2, length 1.0 m, horizontal ---
1200000 chan snglvol
1200101 0.01 1.0 0.01 0.0 0.0 0.0 4.5e-5 0.1128 0
1200200 3 1.55e7 560.0
*
* --- outlet boundary: time dependent volume, 15.5 MPa sink ---
1300000 outlet tmdpvol
1300101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1300200 3
1300201 0.0 1.55e7 560.0
*
* --- junction: channel outlet to outlet boundary ---
1400000 outjun sngljun
1400101 120010000 130010000 0.01 0.0 0.0 0
1400201 1 0.3 0.0 0.0
*
* --- fuel rod heat structure (cylindrical), 1 axial segment, 4 radial nodes ---
*     NH=1 NP=4 geom=2(cyl) init=0 left=0.0 reflood=0 bcv=0 maxax=2
11500000 1 5 2 0 0.0 0 0 2
*     network flag W1=0 (geometry given here), format W2=2 (sequence)
11500100 0 2
*     radial intervals (format 1): number of intervals, right coordinate (m)
*     fuel: 0->2.0 mm, 2.0->4.0 mm ; gap: 4.0->4.1 mm ; clad: 4.1->4.7 mm
11500101 2.0e-3 1
11500102 2.0e-3 2
11500103 1.0e-4 3
11500104 6.0e-4 4
*     composition: interval 1,2 = fuel(mat 1); 3 = gap(mat 2); 4 = cladding(mat 3)
11500201 1 1 1 2 2 3 3 4
*     heat source distribution: only fuel intervals (1,2) have power
11500301 1.0 1 1.0 2 0.0 3 0.0 4
*     initial temperature: 560 K at all 4 nodes
11500401 560.0 1 560.0 2 560.0 3 560.0 4 560.0 5
*     heat source: type 1 (general table 1 = power), multiplier 1.0
11500701 1 1.0 0.0 0.0 1
*     left boundary (r=0): adiabatic/symmetry
11500501 0 0 0 0 0.0 1
*     right boundary (r=4.7mm): convective to coolant volume 120010000
11500601 120010000 0 1 1 0.5 1
*     additional right boundary data (CHF correlation): 9 words
11500901 0.0 10.0 10.0 0.0 0.0 0.0 0.0 1.0 1
*     gap conductance model: initial gap pressure 0.5 MPa, ref volume 120010000
11500001 5.0e5 120010000
*     gap deformation data: fuel roughness, clad roughness, fuel disp, clad disp, hs number
11500011 1.0e-6 1.0e-6 0.0 0.0 1
*
* --- general table 1: total power vs time (constant 30 kW) ---
20200100 power
20200101 0.0 3.0e4
20200102 100.0 3.0e4
*
* --- thermal properties ---
* material 1 = UO2 fuel (built-in)
20100100 uo2
* material 2 = helium gap gas (TBL/FCTN, W2=3 gas mole fractions)
20100200 tbl/fctn 3 1
20100201 helium 1.0
20100251 1.0e6
* material 3 = zirconium cladding (built-in)
20100300 zr
.
