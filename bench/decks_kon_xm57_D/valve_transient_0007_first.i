= TRIGGER VALVE TRANSIENT: 1.0 MPa WATER -> 0.4 MPa SINK, VALVE OPENS AT T=2 s
* system   : two pressure boundaries (tmdpvol) + two single volumes + one TRPVLV valve
* driver   : pressure difference 1.0 MPa - 0.4 MPa = 0.6 MPa after the valve opens
* energy   : adiabatic, no heating; 300 K subcooled water (T_sat(0.4 MPa) ~ 416 K)
* valve    : TRPVLV, full-open area 0.02 m2, closed while trip 401 is false
* expected : mdot(2s) ~ 0 -> ~690 kg/s, P_up ~ 1.0 MPa, P_down ~ 0.4 MPa, T ~ 300 K
100  new  transnt
102  si  si
201  7.0  1.0e-6  2.0e-3  3  25  200  500

* upstream pressure boundary: 1.0 MPa, 300 K
1010000  upsrc  tmdpvol
1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1010200  3
1010201  0.0  1.0e6  300.0

* junction from source into upstream plenum
1020000  upjun  sngljun
1020101  101000000  110000000  0.05  0.0  0.0  0000
1020201  1  0.0  0.0  0.0

* upstream plenum at 1.0 MPa, 300 K
1100000  upvol  snglvol
1100101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1100200  3  1.0e6  300.0

* trigger valve: full open area 0.02 m2, abrupt area change (a=1), choked model on
1200000  trv  valve
1200101  110010000  130000000  0.02  0.0  0.0  000100  1.0  1.0
1200201  1  0.0  0.0  0.0
1200300  trpvlv
1200301  401

* downstream plenum, initially 0.4 MPa, 300 K
1300000  dnvol  snglvol
1300101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1300200  3  0.4e6  300.0

* junction from downstream plenum to the sink
1350000  dnjun  sngljun
1350101  130010000  141000000  0.05  0.0  0.0  0000
1350201  1  0.0  0.0  0.0

* downstream pressure boundary: 0.4 MPa, 300 K
1410000  dnsrc  tmdpvol
1410101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1410200  3
1410201  0.0  0.4e6  300.0

* trip 401: true when time > 2.0 s -> valve opens
401  time  0  gt  null  0  2.0  n
.
