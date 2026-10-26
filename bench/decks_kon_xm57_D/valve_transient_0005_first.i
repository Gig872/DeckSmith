= TRIGGER VALVE TRANSIENT TEST
* Purpose: upstream constant-pressure water (0.8 MPa, 300 K) discharges
* through an initially CLOSED trigger valve into a 0.9 MPa boundary.
* Valve opens at t = 5 s (trip 401), full-open flow area 0.02 m2.
* Transient duration 10 s, tmdpvol/snglvol/sngljun/valve(TRPVLV) only.
* NOTE: downstream pressure (0.9 MPa) is HIGHER than upstream (0.8 MPa),
* so when the valve opens the flow goes BACKWARD (into the upstream side).
100  new  transnt
102  si  si
201  10.0  1.0e-6  0.002  3  10  50  500
*
* --- upstream constant-pressure source: 0.8 MPa, 300 K ---
1010000  inb  tmdpvol
1010101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1010200  3
1010201  0.0  0.8e6  300.0
*
* --- junction from the source into the upstream plenum ---
1020000  inj  sngljun
1020101  101000000  110000000  0.02  0.0  0.0  0000
1020201  1  0.0  0.0  0.0
*
* --- upstream plenum, initially at 0.8 MPa / 300 K (valve shut) ---
1100000  vol  snglvol
1100101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1100200  3  0.8e6  300.0
*
* --- trigger valve: closed while trip 401 is false, opens when true ---
1200000  trv  valve
1200101  110010000  131000000  0.02  0.0  0.0  000100
1200201  1  0.0  0.0  0.0
1200300  trpvlv
1200301  401
*
* --- downstream constant-pressure boundary: 0.9 MPa, 300 K ---
1310000  outb  tmdpvol
1310101  0.05  0.5  0.0  0.0  0.0  0.0  0.0  0.252  0000
1310200  3
1310201  0.0  0.9e6  300.0
*
* --- trip 401: valve OPEN signal, time > 5.0 s ---
401  time  0  gt  null  0  5.0  n
.
