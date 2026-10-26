= PWR SBLOCA blowdown transient
* Single volume (0.2 m3) at 10 MPa, 600 K subcooled water
* Break opens at t=5 s, area 1.0 cm2, discharging to containment
* Containment: 0.1 MPa, 300 K
100 new transnt
102 si si
201 30.0 1.0e-6 0.05 3 1000 10000 0
*
* --- Pressure vessel (single volume) ---
1100000 pv snglvol
1100101 0.2 1.0 0.2 0.0 0.0 0.0 0.0 0.0 0
1100200 3 10.0e6 600.0
*
* --- Containment boundary (time dependent volume) ---
1200000 cont tmdpvol
1200101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1200200 3
1200201 0.0 0.1e6 300.0
*
* --- Break junction (time dependent junction) ---
1300000 brk tmdpjun
1300101 110010000 120010000 1.0e-4
1300200 1
1300201 0.0 0.0 0.0 0.0
1300202 5.0 0.0 0.0 0.0
1300203 5.0 1.0e6 1.0e6 0.0
1300204 30.0 1.0e6 1.0e6 0.0
.
