= Trigger valve transient: 0.8 MPa water -> 0.4 MPa boundary
* Upstream tmdpvol 100 at 0.8 MPa / 300 K
* Trigger valve junction 200 (TRPVLV), initially closed, opens at t=2 s
* Downstream tmdpvol 300 at 0.4 MPa
* Trip 501: time >= 2.0 s
100 new transnt
102 si si
201 7.0 1.0e-6 0.05 3 1000 10000 0
*
*--- Trip: valve opens at t = 2 s ---
501 time 0 gt null 0 2.0 n
*
*--- Upstream pressure boundary (tmdpvol 100) ---
1000000 upstrm tmdpvol
1000101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1000200 3
1000201 0.0 8.0e5 300.0
1000201 7.0 8.0e5 300.0
*
*--- Trigger valve junction (200) ---
2000000 valve trpvlv
2000101 100010000 300000000 0.02 0.0 0.0 0
2000201 0 0.0 0.0 0.0
2000300 trpvlv
2000301 501
*
*--- Downstream pressure boundary (tmdpvol 300) ---
3000000 downst tmdpvol
3000101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
3000200 3
3000201 0.0 4.0e5 300.0
3000201 7.0 4.0e5 300.0
.
