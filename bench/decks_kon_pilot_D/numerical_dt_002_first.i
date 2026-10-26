= PWR SBLOCA blowdown - single volume + break valve
* Scenario: small break LOCA. Primary system lumped into ONE control volume
*   0.2 m3, initial 15 MPa / 600 K subcooled water.
* Break: motor valve (full open area 2.0e-4 m2 = 2.0 cm2) opens at t = 5 s,
*   discharging into a containment boundary at 0.1 MPa / 300 K.
* Choked (critical) two-phase discharge is computed by the RELAP5 choking model
*   (valve flag c=0), no flow is prescribed by hand.
* Transient: 30 s, maximum time step 0.005 s.
*
* --- problem control
100  new  transnt
102  si  si
201  30.0  1.0e-8  0.005  3  20  200  0
*
* --- trips: 501 = break opens at t >= 5 s ; 502 = never closes
501  time  0  ge  null  0  5.0  n
502  time  0  ge  null  0  1.0e10  n
*
* --- primary system (single volume, adiabatic)
*     area 0.1 m2 x length 2.0 m = 0.2 m3, horizontal, no heat structures
1000000  pri  snglvol
1000101  0.1  2.0  0.2  0.0  0.0  0.0  0.0  0.357  0000
1000200  3  15.0e6  600.0
*
* --- containment boundary (constant pressure / temperature sink)
2000000  cont  tmdpvol
2000101  1.0  10.0  10.0  0.0  0.0  0.0  0.0  1.0  0000
2000200  3
2000201  0.0  0.1e6  300.0
*
* --- break valve: primary outlet -> containment
*     area 2.0e-4 m2, losses 0, flag fvcahs = 000100 (abrupt area, choking ON)
3000000  brk  valve
3000101  100010000  200000000  2.0e-4  0.0  0.0  000100  1.0  1.0
3000201  0  0.0  0.0  0.0
3000300  mtrvlv
3000301  501  502  100.0  0.0  0
.
