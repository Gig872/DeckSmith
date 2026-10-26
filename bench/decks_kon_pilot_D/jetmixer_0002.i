= jet mixer steady state, 1.0 MPa drive + 0.8 MPa suction -> 0.7 MPa exit
* single phase liquid water at 300 K, no heat addition (isothermal mixing)
* drive source   100 : tmdpvol 1.0 MPa
* suction source 110 : tmdpvol 0.8 MPa
* mixing chamber 130 : snglvol, flow area 0.005 m2, length 0.2 m
* exit sink     140 : tmdpvol 0.7 MPa
* junction losses (assumption, not given in request):
*   drive 120 K=5.0 (nozzle contraction + sudden expansion)
*   suction 121 K=2.0 (suction line)
*   exit 141 K=1.0 (short exit pipe)
100 new stdy-st
102 si si
201 300.0 1.0e-6 0.05 3 20 50 500
*
*--- constant pressure boundaries
1000000 drive tmdpvol
1000101 0.005 0.5 0.0025 0.0 0.0 0.0 0.0 0.0798 0
1000200 3
1000201 0.0 1.0e6 300.0
1100000 suctn tmdpvol
1100101 0.005 0.5 0.0025 0.0 0.0 0.0 0.0 0.0798 0
1100200 3
1100201 0.0 0.8e6 300.0
1400000 sink tmdpvol
1400101 0.005 0.5 0.0025 0.0 0.0 0.0 0.0 0.0798 0
1400200 3
1400201 0.0 0.7e6 300.0
*
*--- junctions
1200000 jdrive sngljun
1200101 100000000 130000000 0.005 5.0 5.0 0
1200201 1 45.0 0.0 0.0
1210000 jsuctn sngljun
1210101 110000000 130000000 0.005 2.0 2.0 0
1210201 1 19.0 0.0 0.0
1410000 jexit sngljun
1410101 130010000 140000000 0.005 1.0 1.0 0
1410201 1 64.0 0.0 0.0
*
*--- mixing chamber
1300000 mixer snglvol
1300101 0.005 0.2 0.001 0.0 0.0 0.0 0.0 0.0798 0
1300200 3 7.85e5 300.0
.
