= PWR SBLOCA depressurization transient
= Single volume (0.2 m3) at 15 MPa, 600 K subcooled water
= Break opens at t=5 s, area 2.0e-4 m2, discharges to 0.1 MPa / 300 K containment
= Transient duration 30 s, max time step 0.005 s
*
100 new transnt
102 si si
201 30.0 1.0e-6 0.005 3 1 1 1
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
* --- break junction: closed until 5 s, then open (mass flow boundary) ---
1300000 brk tmdpjun
1300101 110010000 120010000 2.0e-4
1300200 1
1300201 0.0 0.0 0.0 0.0
1300202 5.0 0.0 0.0 0.0
1300203 5.0001 1000.0 1000.0 0.0
1300204 30.0 1000.0 1000.0 0.0
.
