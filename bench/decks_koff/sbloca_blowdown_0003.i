= PWR SBLOCA blowdown, single volume 0.2 m3, break 1 cm2 opens at t=10 s
* Transient 30 s.  Vessel: snglvol 100 (0.2 m3, 10 MPa, 550 K subcooled).
* NOTE: user asked 10 MPa/600 K "subcooled water", but at 10 MPa the
*       saturation temperature is only ~584 K, so 600 K would be superheated
*       steam, not subcooled liquid.  Adopted 550 K (34 K subcooling) as the
*       physically consistent subcooled initial state (default, changeable).
* Break: trip valve 300 (area 1e-4 m2) from vessel 100 to containment 200,
*        opens when trip 501 (time >= 10 s) is true; choked flow computed by code.
* Containment: tmdpvol 200 at 0.1 MPa, 300 K.
100 new transnt
102 si si
201 10.0 1.0e-6 0.05 3 20 200 1000
202 10.5 1.0e-6 0.01 3 1 1 1000
203 12.0 1.0e-6 0.01 3 1 1 1000
204 30.0 1.0e-6 0.05 3 20 200 1000
*
* --- trip: break opens at t = 10 s ---
501 time 0 gt null 0 10.0 n
*
* --- vessel (pressurized system) ---
1000000 vessel snglvol
1000101 0.2 1.0 0.2 0.0 0.0 0.0 0.0 0.5 0
1000200 3 1.0e7 550.0
*
* --- containment boundary ---
2000000 contmt tmdpvol
2000101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 1.0 0
2000200 3
2000201 0.0 1.0e5 300.0
*
* --- break: trip valve, opens at t=10 s ---
3000000 break valve
3000101 100010000 200000000 1.0e-4 0.0 0.0 0100000
3000201 0 0.0 0.0 0.0
3000300 trpvlv
3000301 501
.
