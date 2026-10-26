= Trigger valve transient: 0.8 MPa water discharges to 0.4 MPa boundary
= Upstream tmdpvol 0.8 MPa / 300 K feeds a short pipe (real volume)
= Trip valve (TRPVLV) initially closed, opens at t=10 s, area 0.02 m2
= Downstream tmdpvol 0.4 MPa ; transient duration 15 s
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
* --- short pipe (real control volume) between boundary and valve ---
1200000 inlet pipe
1200001 1
1200101 0.02 1
1200301 10.0 1
1200601 0.0 1
1200801 0.0 0.16 1
1201001 0 1
1201201 3 8.0e5 300.0 0 0 0 1
*
* --- connect upstream boundary to pipe inlet ---
1250000 injun sngljun
1250101 110010000 120000000 0.02 0.0 0.0 0
1250201 0 0.0 0.0 0.0
*
* --- downstream boundary: constant 0.4 MPa, 300 K ---
1300000 downstr tmdpvol
1300101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1300200 3
1300201 0.0 4.0e5 300.0
*
* --- trigger valve: from pipe outlet to downstream, opened by trip 401 ---
1400000 tvalve valve
1400101 120010000 130010000 0.02 0.0 0.0 0
1400201 0 0.0 0.0 0.0
1400300 trpvlv
1400301 401
.
