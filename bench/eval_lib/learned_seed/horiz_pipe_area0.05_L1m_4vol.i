* Horizontal pipe steady-state model
* area 0.05 m2, length 1 m, 4 volumes
* inlet 1 MPa / 300 K, outlet 0.9 MPa
100  new  stdy-st
102  si  si
201  10.0  1.0e-6  0.01  3  100  200  500

* inlet time-dependent volume (pressure/temperature boundary)
1010000  inb  tmdpvol
1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1010200  3
1010201  0.0  1.0e6  300.0

* inlet junction (single junction, connects inlet boundary to pipe)
1020000  inj  sngljun
1020101  101000000  110000000  0.05  0.0  0.0  0000
1020201  1  10.0  0.0  0.0

* pipe
1100000  pipe1  pipe
1100001  4
1100101  0.05  4
1100301  0.25  4
1100601  0.0  4
1100801  0.0  0.252  4
1101001  0000000  4
1101101  0  3
1101201  3  1.0e6  300.0  0  0  0  4
1101300  1
1101301  10.0  0.0  0.0  3

* outlet junction
1200000  outj  sngljun
1200101  110010000  121000000  0.05  0.0  0.0  0000
1200201  1  10.0  0.0  0.0

* outlet time-dependent volume (pressure boundary)
1210000  outb  tmdpvol
1210101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1210200  3
1210201  0.0  0.9e6  300.0
.
