= PWR SBLOCA depressurization transient
= Single volume (0.2 m3) at 15 MPa, 600 K subcooled water
= Break (motor valve, 2.0e-4 m2) opens at t=5 s, discharges to 0.1 MPa / 300 K containment
= Transient duration 30 s, max time step 0.005 s
*
100 new transnt
102 si si
201 30.0 1.0e-6 0.005 3 1 1 1
*
* --- trip: break opens at t = 5 s ---
401 time 0 gt null 0 5.0 n
* --- trip: never true (used as dummy close trip) ---
402 time 0 lt null 0 -1.0 n
*
* --- pressurized system: single volume, 0.2 m3, 15 MPa, 600 K ---
1100000 sys snglvol
1100101 1.0 0.2 0.2 0.0 0.0 0.0 0.0 0.0 0
1100200 3 15.0e6 600.0
*
* --- containment boundary: 0.1 MPa, 300 K ---
1200000 cont tmdpvol
1200101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1200200 3
1200201 0.0 1.0e5 300.0
*
* --- break: motor valve, area 2.0e-4 m2, opened by trip 401 at 5 s ---
1300000 brk valve
1300101 110010000 120010000 2.0e-4 0.0 0.0 000100
1300201 1 0.0 0.0 0.0
1300300 mtrvlv
1300301 401 402 100.0 0.0
.
