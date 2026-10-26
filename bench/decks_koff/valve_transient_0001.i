= Trigger valve transient: 0.8 MPa water -> 0.4 MPa boundary
* Upstream tmdpvol 100 at 0.8 MPa / 300 K
* snglvol 200 buffer volume
* Trigger valve junction 250 (TRPVLV), initially closed, opens at t=2 s
* Downstream tmdpvol 300 at 0.4 MPa
* Trip 501: time >= 2.0 s
100 new transnt
102 si si
201 7.0 1.0e-6 0.05 0 1 1 1000
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
*--- Inlet junction (sngljun 150): tmdpvol 100 -> snglvol 200 ---
1500000 inlet sngljun
1500101 100010000 200000000 1.0 0.0 0.0 0
1500201 0 0.0 0.0 0.0
*
*--- Buffer volume (snglvol 200) ---
2000000 buffer snglvol
2000101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
2000200 3 8.0e5 300.0
*
*--- Trigger valve junction (250) ---
2500000 valve valve
2500101 200010000 300000000 0.02 0.0 0.0 0
2500201 0 0.0 0.0 0.0
2500300 trpvlv
2500301 501
*
*--- Downstream pressure boundary (tmdpvol 300) ---
3000000 downst tmdpvol
3000101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
3000200 3
3000201 0.0 4.0e5 300.0
3000201 7.0 4.0e5 300.0
.
