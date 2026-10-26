= NOZZLE CHOKED FLOW - STEADY STATE
* Water at 7.0 MPa / 559.0 K from a fixed-pressure source flows through
* a 1.18 m long, 0.05 m ID pipe nozzle (4 control volumes, roughness
* 4.5e-5 m) and discharges into a 0.1 MPa atmosphere.
* Geometry: A = pi/4*0.05^2 = 1.96350e-3 m2 , cell length = 1.18/4 = 0.295 m
* Driver: pressure difference 7.0 MPa -> 0.1 MPa, exit choked (sonic)
* Adiabatic wall: no heat structure, energy carried by the fluid only.
100  new  stdy-st
102  si  si
201  10.0  1.0e-6  0.005  3  100  200  500
*
*---- upstream fixed-pressure water source : 7.0 MPa , 559.0 K
1000000  srcvol  tmdpvol
1000101  1.96350e-3  0.5  0.0  0.0  0.0  0.0  0.0  0.05  0000
1000200  3
1000201  0.0  7.0e6  559.0
*
*---- inlet connection (no form loss)
1100000  inljun  sngljun
1100101  100000000  120000000  1.96350e-3  0.0  0.0  0000
1100201  1  60.0  0.0  0.0
*
*---- nozzle pipe : 4 control volumes
1200000  nozzle  pipe
1200001  4
1200101  1.96350e-3  4
1200301  0.295  4
1200601  0.0  4
1200801  4.5e-5  0.05  4
1201001  0000000  4
1201101  0  3
1201201  3  6.2e6  548.0  0.0  0.0  0.0  1
1201202  3  5.0e6  535.0  0.0  0.0  0.0  2
1201203  3  3.5e6  514.0  0.0  0.0  0.0  3
1201204  3  1.5e6  469.0  0.0  0.0  0.0  4
1201300  1
1201301  60.0  0.0  0.0  3
*
*---- outlet connection to the atmosphere (choking model active)
1300000  outjun  sngljun
1300101  120010000  140000000  1.96350e-3  0.0  0.0  0000
1300201  1  60.0  0.0  0.0
*
*---- downstream sink : 0.1 MPa
1400000  snkvol  tmdpvol
1400101  1.96350e-3  0.5  0.0  0.0  0.0  0.0  0.0  0.05  0000
1400200  3
1400201  0.0  1.0e5  372.0
.
