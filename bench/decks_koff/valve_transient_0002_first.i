= Trigger valve transient: 0.8 MPa water (300 K) -> 0.4 MPa boundary
= Valve initially closed, opens at t=5 s, area 0.02 m2, 10 s transient
*
*--- Problem control ---
100 new transnt
102 si si
201 10.0 1.0e-6 0.01 3 100 1000
*
*--- Trip: valve opens at t = 5 s ---
401 time 0 gt null 0 5.0 n
*
*--- Upstream boundary: 0.8 MPa, 300 K ---
1100000 upstrm tmdpvol
1100101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1100200 3
1100201 0.0 8.0e5 300.0
*
*--- Downstream boundary: 0.4 MPa ---
1200000 downstrm tmdpvol
1200101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1200200 3
1200201 0.0 4.0e5 300.0
*
*--- Trigger valve between the two boundaries ---
1300000 valve1 valve
1300101 110010000 120010000 0.02 0.0 0.0 0
1300201 1 0.0 0.0 0.0
1300300 trpvlv
1300301 1
*
. 
