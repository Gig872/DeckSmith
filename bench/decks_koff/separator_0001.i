= Steam separator steady-state model
= Inlet: 1.0 MPa, 300 K source, specified mass flow 5 kg/s (tmdpjun)
= Separator vessel: flow area 0.05 m2
= Steam outlet and liquid return each to 0.5 MPa constant-pressure boundary
*
100 new stdy-st
102 si si
201 10.0 1.0e-6 0.1 3 1 1 1
*
* --- inlet source: 1.0 MPa, 300 K ---
1000000 src tmdpvol
1000101 0.05 1.0 0.05 0.0 0.0 0.0 0.0 0.0 0
1000200 3
1000201 0.0 1.0e6 300.0
*
* --- separator vessel: flow area 0.05 m2 ---
1100000 sep snglvol
1100101 0.05 1.0 0.05 0.0 0.0 0.0 0.0 0.0 0
1100200 3 7.5e5 300.0
*
* --- steam outlet boundary: 0.5 MPa ---
1200000 stmout tmdpvol
1200101 0.05 1.0 0.05 0.0 0.0 0.0 0.0 0.0 0
1200200 3
1200201 0.0 5.0e5 300.0
*
* --- liquid return boundary: 0.5 MPa ---
1300000 liqout tmdpvol
1300101 0.05 1.0 0.05 0.0 0.0 0.0 0.0 0.0 0
1300200 3
1300201 0.0 5.0e5 300.0
*
* --- inlet junction: source -> separator, specified 5 kg/s ---
1400000 injun tmdpjun
1400101 100000000 110000000 0.05
1400200 1
1400201 0.0 5.0 5.0 0.0
*
* --- steam outlet junction: separator -> steam boundary ---
1500000 stmjun sngljun
1500101 110010000 120000000 0.05 5.0 5.0 0
1500201 0 0.0 0.0 0.0
*
* --- liquid return junction: separator -> liquid boundary ---
1600000 liqjun sngljun
1600101 110010000 130000000 0.05 5.0 5.0 0
1600201 0 0.0 0.0 0.0
.
