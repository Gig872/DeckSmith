= branch split 1 inlet 2 outlets, steady state, 1.0 MPa / 300 K source -> 0.5 MPa sinks
* system: tmdpvol(1.0 MPa,300 K) -> sngljun -> branch(1 in / 2 out)
*         -> volA / volB -> outlet sngljun -> tmdpvol(0.5 MPa) x2
* driver : 0.5 MPa pressure difference, the two 0.005 m2 split junctions are the throttle
* energy : adiabatic, single phase subcooled liquid (Tsat at 0.5 MPa is about 425 K)
* note   : both branches are geometrically symmetric, so flows are expected to be equal
100  new  stdy-st
102  si  si
201  20.0  1.0e-6  0.01  3  100  200  500

* inlet pressure boundary 1.0 MPa 300 K
1010000  inb  tmdpvol
1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1010200  3
1010201  0.0  1.0e6  300.0

* inlet junction source -> branch inlet
1020000  inj  sngljun
1020101  101000000  110000000  0.02  0.0  0.0  0000
1020201  1  1.0  0.0  0.0

* branch: multi junction splitter, junction 1 = inlet, junctions 2 and 3 = two outlets
1100000  split  branch
1100001  3
1100101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1100200  3  1.0e6  300.0
1101101  101000000  110000000  0.02  0.0  0.0  0000
1102101  110000000  120000000  0.005  0.0  0.0  0000
1103101  110000000  130000000  0.005  0.0  0.0  0000
1101201  1.0  0.0
1102201  1.0  0.0
1103201  1.0  0.0

* branch A control volume
1200000  volA  snglvol
1200101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1200200  3  1.0e6  300.0

* branch B control volume
1300000  volB  snglvol
1300101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1300200  3  1.0e6  300.0

* branch A outlet junction to 0.5 MPa boundary
1210000  outA  sngljun
1210101  120010000  151000000  0.01  0.0  0.0  0000
1210201  1  1.0  0.0  0.0

* branch B outlet junction to 0.5 MPa boundary
1310000  outB  sngljun
1310101  130010000  152000000  0.01  0.0  0.0  0000
1310201  1  1.0  0.0  0.0

* outlet pressure boundary A 0.5 MPa
1510000  outbA  tmdpvol
1510101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1510200  3
1510201  0.0  0.5e6  300.0

* outlet pressure boundary B 0.5 MPa
1520000  outbB  tmdpvol
1520101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1520200  3
1520201  0.0  0.5e6  300.0
.
