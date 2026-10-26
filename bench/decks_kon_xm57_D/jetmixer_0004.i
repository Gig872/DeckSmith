= cross-check: same jet mixer built with a generic BRANCH component
* Purpose: verify the steady-state flow split is not an artifact of the
* JETMIXER component; identical geometry/boundaries/loss coefficients but
* the mixing volume is a BRANCH with three junctions.
100  new  stdy-st
102  si  si
201  20.0  1.0e-6  0.01  3  100  200  500

* ---- motive water source, 1.0 MPa / 300 K ----
1010000  motiv  tmdpvol
1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.2520  0000
1010200  3
1010201  0.0  1.0e6  300.0

* ---- suction water source, 0.9 MPa / 300 K ----
1030000  suctn  tmdpvol
1030101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.2520  0000
1030200  3
1030201  0.0  0.9e6  300.0

* ---- discharge boundary, 0.7 MPa / 300 K ----
1510000  disch  tmdpvol
1510101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.2520  0000
1510200  3
1510201  0.0  0.7e6  300.0

* ---- mixing chamber as generic branch, three junctions ----
1200000  mixb  branch
1200001  3
1200101  0.005  0.5  0.0  0.0  0.0  0.0  0.0  0.0798  0000
1200200  3  0.85e6  300.0
1201101  101000000  120000000  0.005  1.0  1.0  0000
1202101  103000000  120000000  0.005  1.0  1.0  0000
1203101  120010000  151000000  0.005  1.0  1.0  0000
1201201  1.0  0.0
1202201  1.0  0.0
1203201  1.0  0.0
.
