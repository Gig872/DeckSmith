= Fuel rod steady-state heat conduction (fuel/gap/clad) coupled to coolant channel
= Coolant: 15.5 MPa, 560 K, 0.5 kg/s through single volume
= Fuel rod: cylindrical, fuel 0-4.0mm, He gap 4.0-4.1mm (0.5 MPa), clad 4.1-4.7mm
= Fuel heat source 30 kW uniform; gap conductance model
*
100 new stdy-st
102 si si
201 10.0 1.0e-6 0.1 3 1 1 1
*
* ================= coolant channel =================
* --- inlet source volume: 15.5 MPa, 560 K ---
1100000 source tmdpvol
1100101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1100200 3
1100201 0.0 15.5e6 560.0
*
* --- inlet flow boundary: 0.5 kg/s, 560 K ---
1000000 inlet tmdpjun
1000101 110010000 120000000 0.005
1000200 1
1000201 0.0 0.5 0.0 0.0
*
* --- coolant channel: single volume, area 0.005 m2, length 1.0 m ---
1200000 chan snglvol
1200101 0.005 1.0 0.005 0.0 0.0 0.0 0.0 0.0 0
1200200 3 15.5e6 560.0
*
* --- outlet pressure boundary: 15.5 MPa, 560 K ---
1300000 outlet tmdpvol
1300101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1300200 3
1300201 0.0 15.5e6 560.0
*
* --- outlet junction: channel -> outlet boundary ---
1400000 outjun sngljun
1400101 120000000 130010000 0.005 0.0 0.0 0
1400201 1 1.0 0.0 0.0
*
* ================= fuel rod heat structure =================
* --- general HS data: NH=1, NP=4, cylindrical(2), no steady init, left coord 0, no reflood ---
11500000 1 4 2 0 0.0 0 0 2
*
* --- gap conductance model: initial gap pressure 0.5 MPa, ref volume 120 ---
11500001 0.5e6 120010000
*
* --- gap deformation data: fuel rough, clad rough, fuel disp, clad disp, hs no ---
11500011 1.0e-6 2.0e-6 0.0 0.0 1
*
* --- network mesh flag: W1=0 (data with hs), W2=2 (sequence expansion) ---
11500100 0 2
*
* --- radial mesh intervals (format 2: interval width, interval number) ---
11500101 0.004 1
11500102 0.0001 2
11500103 0.0006 3
*
* --- composition data: comp no, interval no (fuel=1, gap=2, clad=3) ---
11500201 1 1
11500202 2 2
11500203 3 3
*
* --- initial temperature: 560 K at all 4 nodes (format 1) ---
11500400 0
11500401 560.0 1
11500402 560.0 2
11500403 560.0 3
11500404 560.0 4
*
* --- radial power distribution: relative values per interval (fuel=1, gap=2, clad=3) ---
11500301 1.0 1
11500302 0.0 2
11500303 0.0 3
*
* --- left boundary (fuel centerline): adiabatic/symmetric ---
11500501 0 0 0 0.0 0.0 1
*
* --- right boundary (clad outer surface): convective to volume 120 ---
11500601 120010000 0 1 1 0.5 1
*
* --- heat source: type 1 (table 1 = 30 kW), multiplier 1.0, hs no 1 ---
11500701 1 1.0 0.0 0.0 1
*
* --- additional right boundary data (CHF correlation): eq diam, fwd/rev lengths, grids, local boiling factor ---
11500901 0.0 10.0 10.0 0.0 0.0 0.0 0.0 1.0 1
*
* ================= material properties =================
* --- fuel: UO2 ---
20100100 uo2
*
* --- gap: helium gas, gap conductance model (W2=3) ---
20100200 TBL HELIUM 1.0
*
* --- clad: zirconium ---
20100300 zr
*
* --- general table 1: fuel rod power vs time (constant 30 kW) ---
20200100 power
20200101 0.0 3.0e4
20200102 100.0 3.0e4
.
