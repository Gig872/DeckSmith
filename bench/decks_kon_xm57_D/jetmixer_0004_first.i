= jet mixer steady state: motive 1.0 MPa, suction 0.9 MPa, discharge 0.7 MPa
* Purpose: steady-state flow split of a jet mixer (eductor) fed by two
* constant-pressure water sources and discharging to a low pressure boundary.
* Structure:
*   tmdpvol(1.0MPa,300K) --jmix junction 1 (motive)--+
*   tmdpvol(0.9MPa,300K) --jmix junction 2 (suction)-+--> JETMIXER
*   JETMIXER --jmix junction 3 (discharge)--> tmdpvol(0.7MPa,300K)
* The JETMIXER component carries its own 3 junctions (N=1 motive, N=2 suction,
* N=3 discharge), so no separate sngljun components are used.
* Mixer flow area 0.005 m2, horizontal (inclination 0, elevation change 0).
* Loss coefficients: fwd=rev=1.0 at all three junctions (base case).
* Working fluid: single-phase subcooled liquid water at 300 K, adiabatic.
100  new  stdy-st
102  si  si
201  20.0  1.0e-6  0.01  3  100  200  500

* ---- motive water source, constant 1.0 MPa / 300 K ----
1010000  motiv  tmdpvol
1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.2520  0000
1010200  3
1010201  0.0  1.0e6  300.0

* ---- suction water source, constant 0.9 MPa / 300 K ----
1030000  suctn  tmdpvol
1030101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.2520  0000
1030200  3
1030201  0.0  0.9e6  300.0

* ---- discharge boundary, constant 0.7 MPa / 300 K ----
1510000  disch  tmdpvol
1510101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.2520  0000
1510200  3
1510201  0.0  0.7e6  300.0

* ---- jet mixer: one volume, three junctions ----
1100000  jmix  jetmixer
1100001  3
1100101  0.005  0.5  0.0  0.0  0.0  0.0  0.0  0.0798  0000
1100200  3  0.85e6  300.0
1101101  101000000  110000000  0.005  1.0  1.0  0000
1102101  103000000  110000000  0.005  1.0  1.0  0000
1103101  110010000  151000000  0.005  1.0  1.0  0000
1101201  1.0  0.0
1102201  1.0  0.0
1103201  1.0  0.0
.
