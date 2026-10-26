= PWR SBLOCA lumped blowdown transient
* Lump primary system as one control volume: V = 0.2 m3 (area 0.2 m2 x length 1.0 m)
* Initial state: 15.0 MPa, 600 K subcooled liquid (T_sat(15 MPa) ~ 615 K)
* Break: equivalent area 2.00 cm2 = 2.0e-4 m2, trip valve, opens at t = 5 s
* Break discharges to containment: 0.1 MPa, 300 K time dependent volume
* Transient 30 s, maximum time step 0.005 s, no heat structures (adiabatic)
100  new  transnt
102  si  si
201  30.0  1.0e-6  0.005  3  200  2000  10000

* ---------- primary system: single lumped volume (0.2 m3) ----------
* 0101: area length volume azimuth inclination elevation roughness hyd.diam flag
1000000  pvol  snglvol
1000101  0.2  1.0  0.0  0.0  0.0  0.0  0.0  0.5046  0000
* 0200: thermal-hydraulic initial condition, code 3 = pressure and temperature
1000200  3  15.0e6  600.0

* ---------- containment: time dependent volume, 0.1 MPa / 300 K ----------
2000000  cnt  tmdpvol
2000101  1.0  10.0  0.0  0.0  0.0  0.0  0.0  1.128  0000
2000200  3
2000201  0.0  1.0e5  300.0

* ---------- break: trip valve, A = 2.0e-4 m2, closed until t = 5 s ----------
* 0101: from to area forward loss reverse loss flag (abrupt area change for valve)
3000000  brk  valve
3000101  100010000  200000000  2.0e-4  0.0  0.0  000100
* 0201: control word 1 = mass flow, initial liquid/vapour mass flow, interface velocity
3000201  1  0.0  0.0  0.0
3000300  trpvlv
3000301  401

* trip 401: time gt 5.0 s  ->  break opens at t = 5 s
401  time  0  gt  null  0  5.0  n
.
