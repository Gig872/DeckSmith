= Jet mixer steady-state model
= Drive source 1.0 MPa, suction source 0.9 MPa, discharge 0.5 MPa
= Mixer flow area 0.005 m2, water at 300 K
= Mixer chamber modeled as a 4-volume pipe (area 0.005 m2, total length 0.4 m)
= Junction loss coefficients represent mixer hydraulic resistance
*
* --- control cards ---
100 new transnt
102 si si
201 20.0 1.0e-6 0.01 3 1 1 1
*
* --- drive source: time dependent volume, 1.0 MPa, 300 K ---
1100000 drvsrc tmdpvol
1100101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1100200 3
1100201 0.0 1.0e6 300.0
*
* --- suction source: time dependent volume, 0.9 MPa, 300 K ---
1200000 suctsrc tmdpvol
1200101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1200200 3
1200201 0.0 9.0e5 300.0
*
* --- discharge boundary: time dependent volume, 0.5 MPa, 300 K ---
1400000 outlet tmdpvol
1400101 1.0 1.0 1.0 0.0 0.0 0.0 0.0 0.0 0
1400200 3
1400201 0.0 5.0e5 300.0
*
* --- mixer chamber: pipe, 4 volumes, area 0.005 m2 ---
1300000 mixer pipe
1300001 4
1300101 0.005 1
1300102 0.005 2
1300103 0.005 3
1300104 0.005 4
1300301 2.5 1
1300302 2.5 2
1300303 2.5 3
1300304 2.5 4
1300601 0.0 1
1300602 0.0 2
1300603 0.0 3
1300604 0.0 4
1300801 0.0 0.0 1
1300802 0.0 0.0 2
1300803 0.0 0.0 3
1300804 0.0 0.0 4
1301001 0 1
1301002 0 2
1301003 0 3
1301004 0 4
1301101 0 1
1301102 0 2
1301103 0 3
1301201 3 6.0e5 300.0 0 0 0 1
1301202 3 6.0e5 300.0 0 0 0 2
1301203 3 6.0e5 300.0 0 0 0 3
1301204 3 6.0e5 300.0 0 0 0 4
1301300 0
1301301 0.0 0.0 0.0 1
1301302 0.0 0.0 0.0 2
1301303 0.0 0.0 0.0 3
*
* --- drive junction: drive source -> mixer inlet ---
1500000 drvjun sngljun
1500101 110010000 130000000 0.005 5.0 5.0 0
1500201 0 0.0 0.0 0.0
*
* --- suction junction: suction source -> mixer inlet ---
1600000 sucjun sngljun
1600101 120010000 130000000 0.005 5.0 5.0 0
1600201 0 0.0 0.0 0.0
*
* --- discharge junction: mixer outlet -> outlet boundary ---
1700000 outjun sngljun
1700101 130010000 140010000 0.005 5.0 5.0 0
1700201 0 0.0 0.0 0.0
.
