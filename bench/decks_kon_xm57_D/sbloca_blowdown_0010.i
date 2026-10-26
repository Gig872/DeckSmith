= PWR SBLOCA blowdown - same model, dtmax = 0.001 s (time step independence check)
100  new  transnt
102  si  si
201  30.0  1.0e-6  0.001  3  100  200  500

* ---------- containment source / sink boundary ----------
1100000  cont  tmdpvol
1100101  10.0  1.0  10.0  0.0  0.0  0.0  0.0  3.568  0000
1100200  3
1100201  0.0  1.0e5  300.0

* ---------- vessel lumped control volume (0.2 m3) ----------
1200000  ves  snglvol
1200101  0.2  1.0  0.2  0.0  0.0  0.0  0.0  0.5046  0000
1200200  3  15.0e6  600.0

* ---------- break: trip valve, 2.0 cm2 ----------
1300000  brk  valve
1300101  120010000  110000000  2.0e-4  0.0  0.0  000100  1.0  1.0
1300201  0  0.0  0.0  0.0
1300300  trpvlv
1300301  401

* trip 401: time > 2.0 s -> break opens
401  time  0  gt  null  0  2.0  n
.
