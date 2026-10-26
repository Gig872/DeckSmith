= PWR SBLOCA lumped blowdown transient - time step independence check (dtmax = 0.0025 s)
100  new  transnt
102  si  si
201  30.0  1.0e-6  0.0025  3  40  400  10000

1000000  pvol  snglvol
1000101  0.2  1.0  0.0  0.0  0.0  0.0  0.0  0.5046  0000
1000200  3  15.0e6  600.0

2000000  cnt  tmdpvol
2000101  1.0  10.0  0.0  0.0  0.0  0.0  0.0  1.128  0000
2000200  3
2000201  0.0  1.0e5  300.0

3000000  brk  valve
3000101  100010000  200000000  2.0e-4  0.0  0.0  000100
3000201  1  0.0  0.0  0.0
3000300  trpvlv
3000301  401

401  time  0  gt  null  0  5.0  n
.
