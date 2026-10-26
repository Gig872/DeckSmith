= PWR SBLOCA blowdown, single volume 0.2 m3, break 1 cm2 at t=10 s
* Transient: 30 s.  System: snglvol 100 (0.2 m3, 10 MPa, 600 K subcooled).
* Break: tmdpjun 300 from vessel 100 to containment 200, mass flow given.
* Containment: tmdpvol 200 at 0.1 MPa, 300 K.
100 new transnt
102 si si
201 30.0 1.0e-6 0.05 3 1000 5000 0
*
* --- vessel (pressurized system) ---
1000000 vessel snglvol
1000101 0.2 1.0 0.2 0.0 0.0 0.0 0.0 0.5 0
1000200 3 1.0e7 600.0
*
* --- containment boundary ---
2000000 contmt tmdpvol
2000101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 1.0 0
2000200 3
2000201 0.0 1.0e5 300.0
*
* --- break (time dependent junction) ---
3000000 break tmdpjun
3000101 100010000 200000000 1.0e-4
3000200 1
3000201 0.0 0.0 0.0 0.0 0.0
3000202 9.999 0.0 0.0 0.0 0.0
3000203 10.0 15.0 15.0 0.0
3000204 30.0 15.0 15.0 0.0
.
