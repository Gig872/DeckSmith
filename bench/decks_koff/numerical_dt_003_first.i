= PWR SBLOCA depressurization transient (single-volume lumped system)
= System: 0.2 m3 single volume, 15 MPa / 600 K subcooled liquid
= Break: trip valve (TRPVLV) area 2.0e-4 m2, opens at t=5 s via trip 401
= Discharge to containment boundary (tmdpvol) at 0.1 MPa / 300 K
= Transient 30 s, max dt 0.001 s
*
* --- control cards ---
100 new transnt
102 si si
201 30.0 1.0e-6 0.001 3 1 1 1
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
