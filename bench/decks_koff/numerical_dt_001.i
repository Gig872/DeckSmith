= PWR SBLOCA depressurization transient
= Single volume (0.2 m3) at 15 MPa / 600 K, break opens at t=5 s
= Break area 2.0e-4 m2 discharging to containment (0.1 MPa, 300 K)
= Transient 30 s, max time step 0.01 s
*
* --- control cards ---
100 new transnt
102 si si
201 30.0 1.0e-6 0.01 3 1 1 1
*
* --- trip: break opens at t = 5 s ---
401 time 0 gt null 0 5.0 n
*
* --- pressurized system: single volume, 0.2 m3, 15 MPa, 600 K ---
1100000 pzr snglvol
1100101 1.0 0.2 0.2 0.0 0.0 0.0 0.0 0.0 0
1100200 3 15.0e6 600.0
*
* --- containment boundary: 0.1 MPa, 300 K ---
1200000 cntn tmdpvol
1200101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1200200 3
1200201 0.0 1.0e5 300.0
*
* --- break: trip valve, area 2.0e-4 m2, opened by trip 401 at t=5 s ---
1300000 brk valve
1300101 110010000 120010000 2.0e-4 0.0 0.0 0
1300201 0 0.0 0.0 0.0
1300300 trpvlv
1300301 401
.
