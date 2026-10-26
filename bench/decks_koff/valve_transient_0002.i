= Trigger valve transient: 0.8 MPa water (300 K) -> 0.4 MPa boundary
= Valve initially closed, opens at t=5 s, area 0.02 m2, 10 s transient
*
*--- Problem control ---
100 new transnt
102 si si
201 10.0 1.0e-6 0.01 3 100 100 1
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
*--- Upstream plenum (real volume) ---
1150000 uplen snglvol
1150101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1150200 3 8.0e5 300.0
*
*--- Downstream plenum (real volume) ---
1250000 dnplen snglvol
1250101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1250200 3 4.0e5 300.0
*
*--- Downstream boundary: 0.4 MPa ---
1200000 downstrm tmdpvol
1200101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1200200 3
1200201 0.0 4.0e5 300.0
*
*--- Junctions linking boundaries to plenums ---
1110000 jup sngljun
1110101 110010000 115000000 1.0 0.0 0.0 0
1110201 1 0.0 0.0 0.0
*
1210000 jdn sngljun
1210101 125010000 120010000 1.0 0.0 0.0 0
1210201 1 0.0 0.0 0.0
*
*--- Trigger valve between the two plenums ---
1300000 valve1 valve
1300101 115010000 125000000 0.02 0.0 0.0 0
1300201 1 0.0 0.0 0.0
1300300 trpvlv
1300301 401
*
. 
