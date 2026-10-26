= pwr sbloca blowdown - lumped primary volume + trip-valve break to containment
* system under pressure : snglvol 001, V=0.2 m3 (A=0.2 m2, L=1.0 m), initial 15 MPa / 600 K subcooled liquid
* containment boundary  : tmdpvol 002, 0.1 MPa / 300 K constant (large source/sink)
* break                 : valve 003 (trpvlv, trip 501), full-open area 2.0e-4 m2, opens at t=5 s
* transient 0~30 s, maximum time step 0.01 s
100  new  transnt
102  si  si
201  30.0  1.0e-6  0.01  3  50  50  5000

*----- primary system: single control volume -----
0010000  core  snglvol
0010101  0.2  1.0  0.2  0.0  0.0  0.0  0.0  0.5  0000
0010200  3  1.5e7  600.0

*----- containment: time dependent volume (pressure/temperature boundary) -----
0020000  cont  tmdpvol
0020101  1.0  1.0  1.0  0.0  0.0  0.0  0.0  1.0  0000
0020200  3
0020201  0.0  1.0e5  300.0

*----- break: trip valve, abrupt area change, choking model on -----
0030000  brk  valve
0030101  001010000  002010000  2.0e-4  0.0  0.0  00100  1.0  1.0
0030201  0  0.0  0.0  0.0
0030300  trpvlv
0030301  501

*----- trip: break opens when t > 5.0 s -----
501  time  0  gt  null  0  5.0  n
.
