= branch splitter steady state model: 1.0 MPa / 300 K water, 1 inlet 2 outlets, sinks at 0.5 MPa
* topology: tmdpvol 101 (1.0 MPa, 300 K)
*           --jn 110-01--> branch 110 (multi junction splitter, 3 junctions: 1 in / 2 out)
*           --jn 110-02--> snglvol 120 (branch A) --sngljun 121--> tmdpvol 151 (0.5 MPa)
*           --jn 110-03--> snglvol 130 (branch B) --sngljun 131--> tmdpvol 152 (0.5 MPa)
* driver : pressure difference 1.0 -> 0.5 MPa; the two 0.005 m2 split junctions are the
*          main throttle, so they carry almost the whole 0.5 MPa drop
* energy : adiabatic, no heat source / no work; single phase subcooled liquid water,
*          Tsat(1.0 MPa)=453 K and Tsat(0.5 MPa)=425 K are both far above 300 K, so no flashing
* split junctions use junction flag 000100 (format fvcahs, digit a=1): abrupt area change,
* so RELAP5 applies the sudden contraction / sudden expansion loss (Kc=0.45, Ke=0.81) plus the
* acceleration (velocity head) term -> total 2.26 velocity heads, which is the energy
* consistent momentum balance for a 0.05 m2 header feeding a 0.005 m2 branch
100  new  stdy-st
102  si  si
201  20.0  1.0e-6  0.01  3  100  200  500

* ---- inlet pressure boundary: 1.0 MPa, 300 K ----
1010000  inb  tmdpvol
1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1010200  3
1010201  0.0  1.0e6  300.0

* ---- splitter: multi junction component, junction 1 inlet, junctions 2 and 3 outlets ----
1100000  split  branch
1100001  3
1100101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1100200  3  1.0e6  300.0
1101101  101000000  110000000  0.02  0.0  0.0  000000
1102101  110010000  120000000  0.005  0.0  0.0  000100
1103101  110010000  130000000  0.005  0.0  0.0  000100
1101201  1.0  0.0
1102201  1.0  0.0
1103201  1.0  0.0

* ---- branch A control volume ----
1200000  volA  snglvol
1200101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1200200  3  1.0e6  300.0

* ---- branch B control volume ----
1300000  volB  snglvol
1300101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1300200  3  1.0e6  300.0

* ---- branch A outlet junction to the 0.5 MPa boundary ----
1210000  outA  sngljun
1210101  120010000  151000000  0.01  0.0  0.0  0000
1210201  1  1.0  0.0  0.0

* ---- branch B outlet junction to the 0.5 MPa boundary ----
1310000  outB  sngljun
1310101  130010000  152000000  0.01  0.0  0.0  0000
1310201  1  1.0  0.0  0.0

* ---- outlet pressure boundary A: 0.5 MPa ----
1510000  outbA  tmdpvol
1510101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1510200  3
1510201  0.0  0.5e6  300.0

* ---- outlet pressure boundary B: 0.5 MPa ----
1520000  outbB  tmdpvol
1520101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1520200  3
1520201  0.0  0.5e6  300.0
.
