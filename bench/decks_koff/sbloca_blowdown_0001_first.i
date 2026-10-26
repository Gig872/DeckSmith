= PWR SBLOCA depressurization transient
= Single volume (0.2 m3) at 10 MPa, 600 K; break opens at t=2 s
= Break area 1.0 cm2 discharging to containment (0.1 MPa, 300 K)
= Transient duration 30 s
*
* --- control cards ---
100 new transnt
102 si si
201 30.0 1.0e-6 0.1 3 1000 10000 0
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
* --- break: time dependent junction from vessel to containment ---
1300000 brk tmdpjun
1300101 110000000 120010000 1.0e-4
1300200 1
1300201 0.0 0.0 0.0 0.0
1300202 2.0 0.0 0.0 0.0
1300203 2.0001 1.0e6 1.0e6 0.0
1300204 30.0 1.0e6 1.0e6 0.0
.
