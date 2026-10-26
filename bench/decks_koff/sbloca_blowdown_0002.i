= PWR SBLOCA blowdown transient
* Single volume (0.2 m3) at 10 MPa, 600 K subcooled water
* Break opens at t=5 s, area 1.0 cm2, discharging to containment
* Containment: 0.1 MPa, 300 K
100 new transnt
102 si si
201 30.0 1.0e-6 0.05 3 100 200 1
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
* --- Break valve (trip valve, opens at t=5 s) ---
1300000 brk valve
1300101 110010000 120010000 1.0e-4 0.0 0.0 0000000
1300201 0 0.0 0.0 0.0
1300300 trpvlv
1300301 501
*
* --- Trip: time > 5.0 s ---
501 time 0 gt null 0 5.0 n
.
