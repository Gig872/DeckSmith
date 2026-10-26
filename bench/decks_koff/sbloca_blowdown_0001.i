= PWR SBLOCA depressurization transient
= Single volume (0.2 m3) at 10 MPa, 600 K; break opens at t=2 s
= Break area 1.0 cm2 discharging to containment (0.1 MPa, 300 K)
= Transient duration 30 s
*
* --- control cards ---
100 new transnt
102 si si
201 30.0 1.0e-6 0.05 3 1 1 1
*
* --- trip: break opens at t=2 s ---
401 time 0 gt null 0 2.0 n
*
* --- pressure vessel: single volume ---
1100000 pvessel snglvol
1100101 0.2 1.0 0.2 0.0 0.0 0.0 0.0 0.0 0
1100200 3 1.0e7 600.0
*
* --- containment boundary: time dependent volume ---
1200000 contain tmdpvol
1200101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1200200 3
1200201 0.0 1.0e5 300.0
*
* --- break: valve from vessel to containment, opened by trip 401 ---
1300000 brk valve
1300101 110000000 120010000 1.0e-4 0.0 0.0 0
1300201 0 0.0 0.0 0.0
1300300 trpvlv
1300301 401
.
