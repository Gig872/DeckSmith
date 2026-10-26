= PWR SBLOCA DEPRESSURIZATION - SINGLE VOLUME + BREAK TO CONTAINMENT
* Transient 0-30 s, break opens at t=5 s
* Primary system: single volume 100, V=0.2 m3, 15 MPa, 600 K subcooled liquid
* Break path: tmdpjun 101 (area 2.0e-4 m2) -> sngljun 102 -> containment tmdpvol 200
* Containment: 0.1 MPa, 300 K
* Break flow is pressure-difference driven, critical (choked) flow model active
100 new transnt
102 si si
201 30.0 1.0e-6 0.005 3 1000 10000 0
*
* ---------------------------------------------------------------
* primary system single volume
* ---------------------------------------------------------------
1000000 pri_vol snglvol
1000101 0.2 1.0 0.2 0.0 0.0 0.0 0.0 0.504 0
1000200 3 15.0e6 600.0
*
* ---------------------------------------------------------------
* break junction (time dependent, opens at 5 s)
* ---------------------------------------------------------------
1010000 brk_tmdp tmdpjun
1010101 100010000 200000000 2.0e-4
1010200 1
1010201 0.0 0.0 0.0 0.0
1010202 5.0 0.0 0.0 0.0
1010203 5.0001 1.0 1.0 0.0
1010204 30.0 1.0 1.0 0.0
*
* ---------------------------------------------------------------
* containment boundary volume
* ---------------------------------------------------------------
2000000 cont tmdpvol
2000101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 1.128 0
2000200 3
2000201 0.0 0.1e6 300.0
.
