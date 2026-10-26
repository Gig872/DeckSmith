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
* --- inlet flow boundary: 0.5 kg/s, 560 K ---
1000000 inlet tmdpjun
1000101 110000000 120000000 0.005
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
* --- general heat structure data: NH=1, NP=4, cylindrical, no reflood ---
1500000 fuelrod
1500001 1 4 2 0 0.0 0 0 2
*
* --- gap conductance model: initial gap pressure 0.5 MPa, ref volume 120 ---
1500001 0.5e6 120000000
*
* --- gap deformation data: fuel roughness, clad roughness, fuel disp, clad disp, hs no ---
1500011 1.0e-6 2.0e-6 0.0 0.0 1
*
* --- network mesh flag: W1=0 (data with hs), W2=2 (sequence expansion) ---
1500100 0 2
*
* --- radial mesh intervals (format 2: interval width, interval number) ---
1500101 0.004 1
1500102 0.0001 2
1500103 0.0006 3
*
* --- composition data: comp no, interval no (fuel=1, gap=2, clad=3) ---
1500201 1 1
1500202 2 2
1500203 3 3
*
* --- initial temperature: 560 K at all 4 nodes (format 1) ---
1500400 0
1500401 560.0 1
1500402 560.0 2
1500403 560.0 3
1500404 560.0 4
*
* --- left boundary (fuel centerline): adiabatic/symmetric ---
1500501 0 0 0 0.0 1
*
* --- right boundary (clad outer surface): convective to volume 120 ---
1500601 120000000 0 1 0 0.0 1
*
* --- heat source: type 0 (none here), multiplier, left/right direct heating, hs no ---
* --- use control variable power via table: type = table number ---
1500701 1 1.0 0.0 0.0 1
*
* ================= material properties =================
* --- fuel: UO2 ---
20100100 UO2
*
* --- gap: helium gas, gap conductance model (W2=3) ---
20100200 TBL 3 1
20100201 HE 1.0
*
* --- clad: zirconium ---
20100300 ZR
.
