= Trigger valve transient: 0.8 MPa water discharges to 0.4 MPa boundary
= Upstream tmdpvol 0.8 MPa / 300 K ; downstream tmdpvol 0.4 MPa
= Trip valve (TRPVLV) initially closed, opens at t=10 s, area 0.02 m2
= Transient duration 15 s
*
* --- control cards ---
100 new transnt
102 si si
201 15.0 1.0e-6 0.05 3 1 1 1
*
* --- trip: valve opens at t=10 s ---
401 time 0 gt null 0 10.0 n
*
* --- upstream boundary: constant 0.8 MPa, 300 K ---
1100000 upstr tmdpvol
1100101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1100200 3
1100201 0.0 8.0e5 300.0
*
* --- downstream boundary: constant 0.4 MPa, 300 K ---
1200000 downstr tmdpvol
1200101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1200200 3
1200201 0.0 4.0e5 300.0
*
* --- trigger valve: from upstream to downstream, opened by trip 401 ---
1300000 tvalve valve
1300101 110010000 120010000 0.02 0.0 0.0 0
1300201 0 0.0 0.0 0.0
1300300 trpvlv
1300301 401
.
