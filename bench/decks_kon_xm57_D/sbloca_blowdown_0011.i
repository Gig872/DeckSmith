= PWR SBLOCA blowdown transient, lumped vessel
= vessel: snglvol 0.2 m3, 15 MPa / 600 K subcooled liquid
= break  : valve (trip 401 at t=5 s), area 2.00e-4 m2 -> containment
= contain: tmdpvol 0.1 MPa / 300 K
= transient 30 s, no external heating (adiabatic blowdown)
100  new  transnt
102  si  si
201  30.0  1.0e-6  0.01  3  100  200  500

*--- primary system: single lumped control volume, 0.2 m3 ---
1100000  sys  snglvol
1100101  0.2  1.0  0.0  0.0  0.0  0.0  0.0  0.505  0000
* init by t=0 option (p, u_liq, u_vap, voidg) so the state stays 600 K subcooled
* u_liq = 1.4748e6 J/kg at 15 MPa/600 K ; u_vap = 2.4558e6 J/kg (saturated vap. 15 MPa)
1100200  0  15.0e6  1.4748e6  2.4558e6  0.0

*--- break: trip-controlled valve, opens at t=5 s, A = 2.00e-4 m2 ---
1200000  brk  valve
1200101  110010000  131000000  2.0e-4  0.0  0.0  000100
1200201  1  1.0  0.0  0.0
1200300  trpvlv
1200301  401

*--- containment: time-dependent volume sink, 0.1 MPa / 300 K ---
1310000  cnt  tmdpvol
1310101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1310200  3
1310201  0.0  0.1e6  300.0

*--- trip: break opens when time > 5.0 s ---
401  time  0  gt  null  0  5.0  n
.
