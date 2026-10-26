= NOZZLE CHOKED FLOW - STEADY STATE (downstream pressure sweep)
* Water at 7.0 MPa / 559.0 K (= saturated liquid) from a fixed-pressure
* source through a 1.18 m , 0.05 m ID pipe nozzle (4 volumes, rough 4.5e-5 m)
* discharging into a reservoir whose pressure is the sweep parameter.
100  new  stdy-st
102  si  si
201  8.0  1.0e-6  0.002  3  100  200  500
*
1000000  srcvol  tmdpvol
1000101  1.96350e-3  0.5  0.0  0.0  0.0  0.0  0.0  0.05  0000
1000200  2
1000201  0.0  7.0e6  0.0
*
1100000  inljun  sngljun
1100101  100000000  120000000  1.96350e-3  0.0  0.0  0000
1100201  1  60.0  0.0  0.0
*
1200000  nozzle  pipe
1200001  4
1200101  1.96350e-3  4
1200301  0.295  4
1200601  0.0  4
1200801  4.5e-5  0.05  4
1201001  0000000  4
1201101  0  3
1201201  2  6.8e6  0.002  0.0  0.0  0.0  1
1201202  2  6.5e6  0.010  0.0  0.0  0.0  2
1201203  2  6.2e6  0.030  0.0  0.0  0.0  3
1201204  2  5.5e6  0.100  0.0  0.0  0.0  4
1201300  1
1201301  60.0  0.0  0.0  3
*
1300000  outjun  sngljun
1300101  120010000  140000000  1.96350e-3  0.0  0.0  0000
1300201  1  60.0  0.0  0.0
*
1400000  snkvol  tmdpvol
1400101  1.96350e-3  0.5  0.0  0.0  0.0  0.0  0.0  0.05  0000
1400200  2
1400201  0.0  {{pdown}}  0.0
.
